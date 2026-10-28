"""Whole-response guard tests; no production policy enabled."""
import asyncio
import json

import pytest
from fastapi import FastAPI
from starlette.responses import StreamingResponse
from app.core.response_limits import ResponseGuard
from tests.test_request_limits import TestClient


async def invoke(app, path='/labs/sql-injection-easy/attempt'):
    sent=[]
    async def receive(): return {'type':'http.request','body':b'','more_body':False}
    async def send(message): sent.append(message)
    await ResponseGuard(app,1024)({'type':'http','method':'POST','path':path},receive,send)
    return sent


@pytest.mark.parametrize('size',[1023,1024,1025])
def test_actual_response_bytes_below_at_above(size):
    async def app(scope,receive,send):
        await send({'type':'http.response.start','status':200,'headers':[(b'content-length',b'1'),(b'x-private',b'hidden'),(b'access-control-allow-origin',b'http://localhost:5173')]})
        await send({'type':'http.response.body','body':b'x'*size})
    sent=asyncio.run(invoke(app))
    assert sent[0]['status']==(503 if size>1024 else 200)
    body=b''.join(m.get('body',b'') for m in sent[1:])
    assert len(body)<=1024
    if size>1024:
        assert json.loads(body)['code']=='response_limit'
        assert (b'x-private',b'hidden') not in sent[0]['headers']
        assert (b'access-control-allow-origin',b'http://localhost:5173') in sent[0]['headers']
    else:
        assert body==b'x'*size
        assert (b'content-length',str(size).encode()) in sent[0]['headers']


def test_stream_is_stopped_without_leaking_success_prefix():
    reached=[]
    async def app(scope,receive,send):
        await send({'type':'http.response.start','status':200,'headers':[]})
        for chunk in (b'secret'*100,b'x'*600,b'never'):
            reached.append(chunk)
            await send({'type':'http.response.body','body':chunk,'more_body':True})
    sent=asyncio.run(invoke(app))
    assert len(reached)==2
    assert sent[0]['status']==503
    assert b'secret' not in sent[1]['body']


def test_unrelated_path_is_not_modified():
    async def app(scope,receive,send):
        await send({'type':'http.response.start','status':200,'headers':[]})
        await send({'type':'http.response.body','body':b'x'*2000})
    sent=asyncio.run(invoke(app,'/health'))
    assert sent[0]['status']==200
    assert len(sent[1]['body'])==2000


def test_starlette_streaming_response_is_cancelled_and_closed():
    app=FastAPI()
    closed=[]
    @app.get('/labs/sample/render')
    async def stream():
        async def body():
            try:
                yield b'a'*700
                yield b'b'*700
                raise AssertionError('must not keep generating after cap')
            finally: closed.append(True)
        return StreamingResponse(body())
    app.add_middleware(ResponseGuard,max_bytes=1024)
    r=TestClient(app).get('/labs/sample/render')
    assert r.status_code==503
    assert r.json()['code']=='response_limit'
    assert closed==[True]


def test_non_limit_stream_errors_are_not_hidden():
    async def app(scope,receive,send): raise RuntimeError('test internal failure')
    with pytest.raises(RuntimeError): asyncio.run(invoke(app))


def test_limit_must_fit_fixed_error_response():
    with pytest.raises(ValueError): ResponseGuard(None,1)


@pytest.mark.parametrize('messages', [
    [{'type':'http.response.start','status':200,'headers':[]}, {'type':'http.response.body','body':b'partial','more_body':True}],
    [{'type':'http.response.body','body':b'body before start'}],
    [{'type':'http.response.start','status':200,'headers':[]}, {'type':'http.response.start','status':200,'headers':[]}, {'type':'http.response.body','body':b'wrong'}],
])
def test_incomplete_or_invalid_stream_is_never_normalized_to_success(messages):
    async def app(scope,receive,send):
        for message in messages: await send(message)
    with pytest.raises(RuntimeError): asyncio.run(invoke(app))


def test_no_buffered_response_is_sent_after_observed_disconnect():
    async def scenario():
        sent=[]
        async def app(scope,receive,send):
            await send({'type':'http.response.start','status':200,'headers':[]})
            await send({'type':'http.response.body','body':b'partial','more_body':True})
            assert (await receive())['type']=='http.disconnect'
        async def receive(): return {'type':'http.disconnect'}
        async def send(message): sent.append(message)
        await ResponseGuard(app,1024)({'type':'http','method':'GET','path':'/labs/sample/render'},receive,send)
        assert sent==[]
    asyncio.run(scenario())


def test_real_starlette_stream_disconnect_discards_prefix_and_closes_generator():
    async def scenario():
        yielded=asyncio.Event()
        closed=[]
        async def body():
            try:
                yielded.set()
                yield b'private prefix'
                await asyncio.sleep(10)
            finally: closed.append(True)
        sent=[]
        async def receive():
            await yielded.wait()
            return {'type':'http.disconnect'}
        async def send(message): sent.append(message)
        app=StreamingResponse(body())
        await ResponseGuard(app,1024)({'type':'http','method':'GET','path':'/labs/sample/render'},receive,send)
        assert sent==[]
        assert closed==[True]
    asyncio.run(scenario())


@pytest.mark.parametrize('count',[255,256,257])
def test_cap_counts_utf8_bytes_instead_of_characters(count):
    async def app(scope,receive,send):
        await send({'type':'http.response.start','status':200,'headers':[]})
        await send({'type':'http.response.body','body':('😀'*count).encode()})
    sent=asyncio.run(invoke(app))
    assert sent[0]['status']==(503 if count>256 else 200)


def test_mixed_stream_error_group_is_not_misreported_as_size_limit():
    async def app(scope,receive,send):
        await send({'type':'http.response.start','status':200,'headers':[]})
        try:
            await send({'type':'http.response.body','body':b'x'*2000})
        except Exception as limit:
            raise ExceptionGroup('mixed failure',[limit,RuntimeError('cleanup fault')])
    with pytest.raises(ExceptionGroup) as caught:
        asyncio.run(invoke(app))
    assert any(isinstance(e,RuntimeError) for e in caught.value.exceptions)
