"""Injectable #42 response byte cap; not installed in the production app.

Buffer a bounded response before releasing success headers. This does not
prevent an upstream handler from allocating its response before ASGI send.
"""
import json
from app.core.lab_paths import lab_route


class _ResponseTooLarge(Exception):
    pass


def _only_limit_errors(error):
    if isinstance(error, BaseExceptionGroup):
        return all(_only_limit_errors(child) for child in error.exceptions)
    return isinstance(error, _ResponseTooLarge)


class ResponseGuard:
    FAILURE = json.dumps({
        'code': 'response_limit',
        'detail': '결과가 표시 가능한 크기를 넘었습니다. 입력 범위를 줄여 다시 시도하세요.',
    }, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

    def __init__(self, app, max_bytes):
        if type(max_bytes) is not int or max_bytes < len(self.FAILURE):
            raise ValueError('response cap must fit the fixed error response')
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or not lab_route(scope):
            return await self.app(scope, receive, send)
        start = None
        complete = False
        disconnected = False
        body = bytearray()
        async def bounded_send(message):
            nonlocal start, complete
            if message['type'] == 'http.response.start':
                if start is not None or complete:
                    raise RuntimeError('downstream response started twice')
                start = dict(message)
                return
            if message['type'] == 'http.response.body':
                if start is None or complete:
                    raise RuntimeError('downstream response body out of order')
                chunk = message.get('body', b'')
                if len(body) + len(chunk) > self.max_bytes:
                    raise _ResponseTooLarge()
                body.extend(chunk)
                complete = not message.get('more_body', False)
                return
            raise RuntimeError('unsupported ASGI response message')
        async def tracked_receive():
            nonlocal disconnected
            message = await receive()
            if message['type'] == 'http.disconnect':
                disconnected = True
            return message
        exceeded = False
        try:
            await self.app(scope, tracked_receive, bounded_send)
        except (_ResponseTooLarge, BaseExceptionGroup) as exc:
            # AnyIO/Starlette can wrap streaming sender errors in a task group.
            # Do not hide unrelated faults bundled with a limit error.
            if not _only_limit_errors(exc): raise
            exceeded = True
        if disconnected:
            return
        if exceeded:
            # Original headers/body may expose partial success or be inconsistent
            # with JSON. Preserve only already-computed CORS metadata.
            cors = [(k,v) for k,v in (start or {}).get('headers', [])
                    if k.lower().startswith(b'access-control-') or k.lower() == b'vary']
            await send({'type': 'http.response.start', 'status': 503, 'headers': [
                (b'content-type', b'application/json; charset=utf-8'),
                (b'content-length', str(len(self.FAILURE)).encode()),
                *cors,
            ]})
            await send({'type': 'http.response.body', 'body': self.FAILURE})
            return
        if start is None or not complete:
            raise RuntimeError('downstream response did not finish')
        if scope.get('method') != 'HEAD' and start['status'] not in (204, 304):
            headers = [(k,v) for k,v in start.get('headers', [])
                       if k.lower() not in (b'content-length', b'transfer-encoding')]
            start['headers'] = [*headers, (b'content-length', str(len(body)).encode())]
        await send(start)
        await send({'type': 'http.response.body', 'body': bytes(body), 'more_body': False})
