"""Real loopback HTTP against an explicitly configured test app, not production."""
import http.client
import json
import socket
import threading
import time
from urllib.parse import urlencode

import pytest
from fastapi import FastAPI
from starlette.responses import Response
from app.core.response_limits import ResponseGuard
import uvicorn

from app.core.request_limits import InputGuard
from app.routes.labs import router
from tests.test_request_limits import LIMITS


@pytest.fixture(scope='module')
def address():
    app = FastAPI()
    @app.post('/labs/response-probe/attempt')
    def response_probe(payload: dict):
        return Response(b'x'*payload['size'], media_type='application/octet-stream')
    app.include_router(router)
    app.add_middleware(InputGuard, limits=LIMITS)
    app.add_middleware(ResponseGuard, max_bytes=262144)
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, log_level='error', lifespan='off', ws='none'))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic()+5
        while not server.started:
            if not thread.is_alive() or time.monotonic() >= deadline:
                raise RuntimeError('test server did not start')
            time.sleep(.01)
        yield ('127.0.0.1', port)
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        sock.close()
        assert not thread.is_alive(), 'test server did not shut down'


def request(address, method, path, body=None, chunked=False):
    conn = http.client.HTTPConnection(*address, timeout=5)
    try:
        conn.request(method, path, body=body, headers={'Content-Type': 'application/json'}, encode_chunked=chunked)
        response = conn.getresponse()
        return response.status, response.read()
    finally:
        conn.close()


@pytest.mark.parametrize('n', [1999,2000,2001])
@pytest.mark.parametrize('action', ['analyze','attempt'])
def test_real_http_unicode_input_boundary(address,n,action):
    raw=json.dumps({'username':'박'*n},ensure_ascii=False).encode()
    status,body=request(address,'POST','/labs/sql-injection-easy/'+action,raw)
    assert status == (422 if n>2000 else 200)
    if n<=2000:
        value=json.loads(body)
        trace=value if action=='analyze' else value['learning_trace']
        assert trace['raw_input']=='박'*n


@pytest.mark.parametrize('size', [32767,32768,32769])
def test_real_http_chunked_body_boundary(address,size):
    body=b'{"username":""}'
    body+=b' '*(size-len(body))
    chunks=[body[:16000],body[16000:]]
    status,_=request(address,'POST','/labs/sql-injection-easy/analyze',iter(chunks),True)
    assert status==(413 if size>32768 else 200)


@pytest.mark.parametrize('n', [1999,2000,2001])
def test_real_http_render_decoded_length(address,n):
    query=urlencode({'query':'😀'*n})
    status,body=request(address,'GET','/labs/reflected-xss-easy/render?'+query)
    assert status==(422 if n>2000 else 200)


def test_real_http_reject_then_normal_sql_recovers(address):
    path='/labs/sql-injection-easy/attempt'
    status,_=request(address,'POST',path,b'{"username":"a","username":"b"}')
    assert status==422
    raw=json.dumps({'username':"admin' OR '1'='1'--"}).encode()
    status,body=request(address,'POST',path,raw)
    assert status==200 and json.loads(body)['success']


@pytest.mark.parametrize('size',[262143,262144,262145])
def test_real_http_response_cap(address,size):
    status,body=request(address,'POST','/labs/response-probe/attempt',json.dumps({'size':size}).encode())
    assert status==(503 if size>262144 else 200)
    if size>262144:
        assert json.loads(body)['code']=='response_limit'
        assert len(body)<262144
    else: assert body==b'x'*size


def test_real_http_response_rejection_preserves_following_request(address):
    conn=http.client.HTTPConnection(*address,timeout=5)
    try:
        conn.request('POST','/labs/response-probe/attempt',json.dumps({'size':262145}),headers={'content-type':'application/json'})
        first=conn.getresponse()
        assert first.status==503
        assert json.loads(first.read())['code']=='response_limit'
        conn.request('POST','/labs/sql-injection-easy/attempt',json.dumps({'username':"admin' OR '1'='1'--"}),headers={'content-type':'application/json'})
        second=conn.getresponse()
        assert second.status==200 and json.loads(second.read())['success']
    finally: conn.close()
