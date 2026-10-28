"""#42 proposed policy injected into tests; production app is not activated."""
import asyncio
import json

import pytest
from fastapi import FastAPI
from types import SimpleNamespace
from urllib.parse import urlencode, urlsplit

from app.core.request_limits import InputLimits, InputRejected, InputGuard, validate_payload
from app.labs.practice_extensions import PERMISSION_COMMANDS
from app.routes.labs import router

LIMITS = InputLimits(2000, 32768, 40, 2000, (1 << 53) - 1, frozenset(PERMISSION_COMMANDS))


class TestClient:
    __test__ = False

    def __init__(self, app): self.app = app

    def request(self, method, path, *, json=None, content=None, headers=None, params=None):
        parts = urlsplit(path)
        query = urlencode(params) if params else parts.query
        raw = content if content is not None else b'' if json is None else __import__('json').dumps(json, ensure_ascii=False).encode()
        async def invoke():
            incoming = iter([{'type': 'http.request', 'body': raw, 'more_body': False}])
            async def receive():
                try: return next(incoming)
                except StopIteration:
                    # A live client remains connected after sending its request.
                    # Starlette cancels this listener when streaming completes.
                    return await asyncio.Future()
            sent = []
            async def send(message): sent.append(message)
            scope = dict(type='http', asgi={'version': '3.0'}, http_version='1.1', method=method, scheme='http', path=parts.path, raw_path=parts.path.encode(), root_path='', query_string=query.encode(), headers=[(k.lower().encode(), v.encode()) for k,v in (headers or {'content-type': 'application/json'}).items()], server=('test',80), client=('127.0.0.1',1))
            await self.app(scope, receive, send)
            body=b''.join(x.get('body',b'') for x in sent if x['type']=='http.response.body')
            return SimpleNamespace(status_code=sent[0]['status'], text=body.decode(), json=lambda: __import__('json').loads(body))
        return asyncio.run(invoke())

    def post(self, path, **kwargs): return self.request('POST', path, **kwargs)
    def get(self, path, **kwargs): return self.request('GET', path, **kwargs)


def client():
    app = FastAPI()
    app.include_router(router)
    app.add_middleware(InputGuard, limits=LIMITS)
    return TestClient(app)


@pytest.mark.parametrize('count', [1999, 2000, 2001])
@pytest.mark.parametrize('route', ['analyze', 'attempt'])
def test_string_boundary_is_not_truncated(count, route):
    response = client().post('/labs/sql-injection-easy/' + route, json={'username': '박' * count})
    assert response.status_code == (422 if count > 2000 else 200)
    if count <= 2000:
        trace = response.json() if route == 'analyze' else response.json()['learning_trace']
        assert trace['raw_input'] == '박' * count


@pytest.mark.parametrize('payload', [{'username': None}, {'username': True}, {'username': []}, {'username': {}}, {'username': 3}, {'username': 'admin', 'extra': 'x'}, {'history': []}])
def test_types_and_unexpected_fields_are_rejected(payload):
    r = client().post('/labs/sql-injection-easy/analyze', json=payload)
    assert r.status_code == 422
    assert set(r.json()) == {'detail'}
    assert 'admin' not in r.text


@pytest.mark.parametrize('value', [True, False, None, [], {}, '1043', -1, 1 << 53])
def test_idor_rejects_non_integer_or_unrepresentable_id(value):
    assert client().post('/labs/idor-easy/attempt', json={'requested_id': value}).status_code == 422


def test_idor_owner_claim_and_actual_ssrf_field():
    c = client()
    assert c.post('/labs/idor-medium/attempt', json={'requested_id': 1043, 'claimed_user_id': 2001}).json()['success']
    assert c.post('/labs/ssrf-easy/attempt', json={'target_url': 'http://127.0.0.1/admin'}).status_code == 200
    assert c.post('/labs/ssrf-easy/attempt', json={'url': 'http://127.0.0.1/admin'}).status_code == 422


@pytest.mark.parametrize('history,expected', [(['whoami'] * 39, 200), (['whoami'] * 40, 200), (['whoami'] * 41, 422), ([True], 422), ('whoami', 422), (['unknown'], 422)])
def test_history_count_and_commands(history, expected):
    assert client().post('/labs/permissions-easy/attempt', json={'command': 'whoami', 'history': history}).status_code == expected


def test_history_total_boundary_and_no_mutation():
    limits = InputLimits(10, 1000, 10, 10, 10000, frozenset({'a', 'aa', 'aaa'}))
    for count in (9, 10, 11):
        payload = {'command': 'id', 'history': ['aaa', 'aaa', 'aa', 'a' * (count - 8)]}
        if count <= 10:
            validate_payload('permissions-easy', payload, limits)
        else:
            with pytest.raises(InputRejected): validate_payload('permissions-easy', payload, limits)
        assert sum(map(len, payload['history'])) == count


@pytest.mark.parametrize('raw', [b'{', b'[]', b'null', b'{"username":NaN}', b'{"username":"a","username":"b"}', b'{"username":"\xff"}', b'{"username":"\\ud800"}', b'{"username":Infinity}'])
def test_bad_json_has_fixed_error_without_input_echo(raw):
    r = client().post('/labs/sql-injection-easy/attempt', content=raw, headers={'content-type': 'application/json'})
    assert r.status_code == 422
    assert r.json() == {'detail': '입력 형식 또는 허용 범위를 확인하세요.'}


@pytest.mark.parametrize('size', [32767, 32768, 32769])
def test_body_bytes_including_whitespace(size):
    raw = b'{"username":""}'
    raw += b' ' * (size - len(raw))
    r = client().post('/labs/sql-injection-easy/analyze', content=raw, headers={'content-type': 'application/json'})
    assert r.status_code == (413 if size > 32768 else 200)


def test_chunked_actual_bytes_are_counted_without_trusting_content_length():
    async def scenario():
        called = False
        async def downstream(scope, receive, send):
            nonlocal called
            called = True
        messages = iter([{'type': 'http.request', 'body': b' ' * 16000, 'more_body': True}, {'type': 'http.request', 'body': b' ' * 17000, 'more_body': False}])
        async def receive(): return next(messages)
        sent = []
        async def send(message): sent.append(message)
        await InputGuard(downstream, LIMITS)({'type': 'http', 'method': 'POST', 'path': '/labs/sql-injection-easy/attempt', 'headers': [(b'content-length', b'1')]}, receive, send)
        assert not called
        assert sent[0]['status'] == 413
    asyncio.run(scenario())


def test_render_decoded_unicode_length_duplicates_and_invalid_encoding():
    c = client()
    for n in (1999, 2000, 2001):
        assert c.get('/labs/reflected-xss-easy/render', params={'query': '박' * n}).status_code == (422 if n > 2000 else 200)
    assert c.get('/labs/reflected-xss-easy/render?query=a&query=b').status_code == 422
    assert c.get('/labs/reflected-xss-easy/render?query=%FF').status_code == 422
    assert c.get('/labs/reflected-xss-easy/render?query=%ED%A0%80').status_code == 422


def test_success_and_normal_filter_are_preserved():
    c = client()
    p = {'username': "admin' OR '1'='1'--"}
    assert c.post('/labs/sql-injection-easy/attempt', json=p).json()['success']
    assert not c.post('/labs/sql-injection-medium/attempt', json=p).json()['success']
    assert c.post('/labs/sql-injection-medium/attempt', json={'username': "admin' oR '1'='1'--"}).json()['success']


@pytest.mark.parametrize('lab,payload', [
    ('reflected-xss-easy', {'query':'hello'}),
    ('reflected-xss-medium', {'query':'<script></script>'}),
    ('ssrf-easy', {'target_url':'http://127.0.0.1/admin'}),
    ('ssrf-medium', {'target_url':'http://preview.lab.invalid@127.0.0.1/admin'}),
    ('command-injection-easy', {'hostname':'example.com;whoami'}),
    ('command-injection-medium', {'hostname':'example.com && whoami'}),
    ('linux-basics-easy', {'command':'ls'}),
    ('linux-basics-medium', {'command':'ls -l /lab'}),
    ('permissions-easy', {'command':'whoami','history':['id','whoami']}),
])
def test_other_registered_lab_fields_are_preserved(lab,payload):
    for action in ('analyze','attempt'):
        assert client().post('/labs/'+lab+'/'+action,json=payload).status_code==200


def test_disconnect_during_body_does_not_invoke_lab():
    async def scenario():
        called=False
        async def downstream(*args):
            nonlocal called
            called=True
        messages=iter([{'type':'http.request','body':b'{','more_body':True},{'type':'http.disconnect'}])
        async def receive(): return next(messages)
        async def send(message): raise AssertionError('response to disconnected client')
        await InputGuard(downstream,LIMITS)({'type':'http','method':'POST','path':'/labs/sql-injection-easy/attempt'},receive,send)
        assert not called
    asyncio.run(scenario())
