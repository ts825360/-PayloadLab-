"""Injectable #42 input guard. Not installed in the production app pending review.

No production thresholds are selected here; the caller must supply policy.
"""
from dataclasses import dataclass
import json
from app.core.lab_paths import lab_route
from urllib.parse import parse_qsl


@dataclass(frozen=True)
class InputLimits:
    input_chars: int
    body_bytes: int
    history_count: int
    history_chars: int
    identifier_max: int
    history_commands: frozenset[str]

    def __post_init__(self):
        for value in (self.input_chars, self.body_bytes, self.history_count, self.history_chars, self.identifier_max):
            if type(value) is not int or value <= 0:
                raise ValueError('limits must be positive integers')


class InputRejected(ValueError):
    def __init__(self, status=422):
        self.status = status
        super().__init__('input rejected')


_FIELDS = {}
for _category, _field, _levels in (
    ('sql-injection', 'username', ('easy', 'medium')),
    ('reflected-xss', 'query', ('easy', 'medium')),
    ('idor', 'requested_id', ('easy', 'medium')),
    ('ssrf', 'target_url', ('easy', 'medium')),
    ('command-injection', 'hostname', ('easy', 'medium')),
    ('linux-basics', 'command', ('easy', 'medium')),
    ('permissions', 'command', ('easy',)),
):
    for _level in _levels:
        _FIELDS[f'{_category}-{_level}'] = _field


def _string(value, maximum):
    if type(value) is not str or len(value) > maximum:
        raise InputRejected()
    try:
        value.encode('utf-8')
    except UnicodeError:
        raise InputRejected() from None


def validate_payload(lab_id, payload, limits):
    field = _FIELDS.get(lab_id)
    if field is None:
        return  # Existing route keeps responsibility for unknown lab 404.
    if type(payload) is not dict:
        raise InputRejected()
    allowed = {field}
    if lab_id == 'idor-medium': allowed.add('claimed_user_id')
    if lab_id == 'permissions-easy': allowed.add('history')
    if payload.keys() - allowed:
        raise InputRejected()
    if field == 'requested_id':
        for key in ('requested_id', 'claimed_user_id'):
            if key == 'claimed_user_id' and key not in payload: continue
            value = payload.get(key)
            if type(value) is not int or not 0 <= value <= limits.identifier_max:
                raise InputRejected()
    else:
        _string(payload.get(field, ''), limits.input_chars)
    if 'history' in payload:
        history = payload['history']
        if type(history) is not list or len(history) > limits.history_count:
            raise InputRejected()
        total = 0
        for command in history:
            _string(command, limits.input_chars)
            total += len(command)
            if total > limits.history_chars or command.strip() not in limits.history_commands:
                raise InputRejected()
    return payload


def _pairs(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj: raise InputRejected()
        obj[key] = value
    return obj


def _constant(value):
    raise InputRejected()


class InputGuard:
    """Count actual ASGI bytes before JSON decoding and before lab invocation.

    Does not bound upstream web-server buffers, socket timeouts or response size.
    It deliberately does not trust Content-Length and does not truncate input.
    """
    def __init__(self, app, limits):
        self.app, self.limits = app, limits

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        match = lab_route(scope)
        if not match:
            return await self.app(scope, receive, send)
        lab_id, action = match.groups()
        method = scope.get('method')
        if (action == 'render' and method != 'GET') or (action != 'render' and method != 'POST'):
            return await self.app(scope, receive, send)
        replay_receive = receive
        try:
            if action == 'render':
                query = scope.get('query_string', b'')
                if len(query) > self.limits.body_bytes: raise InputRejected(413)
                pairs = parse_qsl(query.decode('ascii'), keep_blank_values=True, encoding='utf-8', errors='strict', max_num_fields=8)
                payload = _pairs(pairs)
                # Only XSS has a renderer; preserve other labs' existing 404.
                if lab_id.startswith('reflected-xss-'):
                    validate_payload(lab_id, payload, self.limits)
            else:
                body = bytearray()
                while True:
                    message = await receive()
                    if message['type'] == 'http.disconnect': return
                    chunk = message.get('body', b'')
                    if len(body) + len(chunk) > self.limits.body_bytes:
                        raise InputRejected(413)
                    body.extend(chunk)
                    if not message.get('more_body', False): break
                payload = json.loads(body.decode('utf-8'), object_pairs_hook=_pairs, parse_constant=_constant)
                validate_payload(lab_id, payload, self.limits)
                replayed = False
                async def replay_receive():
                    nonlocal replayed
                    if not replayed:
                        replayed = True
                        return {'type': 'http.request', 'body': bytes(body), 'more_body': False}
                    return await receive()
        except (InputRejected, ValueError, UnicodeError, RecursionError) as exc:
            status = exc.status if isinstance(exc, InputRejected) else 422
            text = '요청 크기 상한을 초과했습니다.' if status == 413 else '입력 형식 또는 허용 범위를 확인하세요.'
            response = json.dumps({'detail': text}, ensure_ascii=False).encode('utf-8')
            await send({'type': 'http.response.start', 'status': status, 'headers': [(b'content-type', b'application/json; charset=utf-8'), (b'content-length', str(len(response)).encode())]})
            await send({'type': 'http.response.body', 'body': response})
            return
        await self.app(scope, replay_receive, send)
