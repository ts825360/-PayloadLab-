"""Policy-injected review app; default production app remains unconfigured."""
from concurrent.futures import ThreadPoolExecutor
import json
import socket
import threading
import time

import pytest
import uvicorn
from tests.test_request_limits_http import request

from app.review_app import create_review_app
from app.core.sql_limits import SQLLimits
from tests.test_request_limits import LIMITS as INPUT, TestClient
from tests.test_sql_limits import authorize

SQL=SQLLimits(8192,80,128,8192,32768,32768,8192)
HEAVY="' OR (WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n WHERE x<10000) SELECT sum(x) FROM n)>0--"


def client(limits=SQL): return TestClient(create_review_app(input_limits=INPUT,sql_limits=limits,sql_authorizer=authorize,response_bytes=262144))


def test_review_app_preserves_easy_and_normal():
    c=client()
    payload={'username':"admin' OR '1'='1'--"}
    assert c.post('/labs/sql-injection-easy/attempt',json=payload).json()['success']
    assert not c.post('/labs/sql-injection-medium/attempt',json=payload).json()['success']
    assert c.post('/labs/sql-injection-medium/attempt',json={'username':"admin' oR '1'='1'--"}).json()['success']


def test_row_limit_is_not_login_success_or_syntax_error():
    c=client(SQLLimits(8192,80,2,8192,32768,32768,8192))
    value=c.post('/labs/sql-injection-easy/attempt',json={'username':"admin' OR 1=1 UNION ALL SELECT 3,'learner','dummy'--"}).json()
    assert value['success'] is False
    assert value['learning_trace']['execution']['status']=='resource_limit'
    assert value['learning_trace']['execution']['count']==0
    assert value['learning_trace']['lens']['id']=='resource_limit'
    assert value['flow_nodes'] is None


def test_vm_interruption_is_request_local_and_recovers():
    c=client()
    first=c.post('/labs/sql-injection-easy/attempt',json={'username':HEAVY}).json()
    assert first['success'] is False
    assert first['learning_trace']['execution']['status']=='resource_limit'
    assert first['learning_trace']['table'] is None
    second=c.post('/labs/sql-injection-easy/attempt',json={'username':"admin' OR 1=1--"}).json()
    assert second['success'] and second['learning_trace']['execution']['count']==2


def test_analysis_limit_is_not_claimed_as_execution():
    c=client(SQLLimits(64,80,128,8192,32768,32768,8192))
    value=c.post('/labs/sql-injection-easy/analyze',json={'username':'admin'}).json()
    assert value['phase']=='analysis'
    assert value['execution'] is None
    assert value['analysis_status']=='resource_limit'
    assert value['lens']['id']=='resource_limit'
    assert value['table'] is None


def test_authorizer_block_is_not_sql_syntax_or_resource_limit():
    value=client().post('/labs/sql-injection-easy/attempt',json={'username':"' UNION SELECT 3,sqlite_version(),''--"}).json()
    assert not value['success']
    assert value['learning_trace']['execution']['status']=='blocked'
    assert value['learning_trace']['lens']['id']=='operation_blocked'


def test_guarded_review_app_also_rejects_bad_input_before_sql():
    c=client()
    assert c.post('/labs/sql-injection-easy/attempt',json={'username':True}).status_code==422
    assert c.post('/labs/sql-injection-easy/analyze',json={'username':'a'*2001}).status_code==422


def test_parallel_requests_do_not_share_budget_or_failure():
    c=client()
    def call(raw): return c.post('/labs/sql-injection-easy/attempt',json={'username':raw}).json()
    with ThreadPoolExecutor(max_workers=2) as pool:
        values=list(pool.map(call,[HEAVY,"admin' OR 1=1--",HEAVY,"admin' OR 1=1--"]))
    assert [v['success'] for v in values]==[False,True,False,True]


@pytest.fixture(scope='module')
def review_address():
    from fastapi import FastAPI
    app=FastAPI()
    app.mount('/api',create_review_app(input_limits=INPUT,sql_limits=SQL,sql_authorizer=authorize,response_bytes=262144))
    app.mount('/limited-api',create_review_app(input_limits=INPUT,sql_limits=SQL,sql_authorizer=authorize,response_bytes=1024))
    app.mount('/',create_review_app(input_limits=INPUT,sql_limits=SQL,sql_authorizer=authorize,response_bytes=262144))
    sock=socket.socket();sock.bind(('127.0.0.1',0))
    port=sock.getsockname()[1]
    server=uvicorn.Server(uvicorn.Config(app,log_level='error',lifespan='off',ws='none'))
    thread=threading.Thread(target=server.run,kwargs={'sockets':[sock]},daemon=True)
    thread.start()
    try:
        deadline=time.monotonic()+5
        while not server.started:
            if not thread.is_alive() or time.monotonic()>deadline: raise RuntimeError('review server startup failed')
            time.sleep(.01)
        yield ('127.0.0.1',port)
    finally:
        server.should_exit=True;thread.join(5);sock.close()
        assert not thread.is_alive()


def test_real_http_combined_guards_stop_sql_and_recover(review_address):
    path='/labs/sql-injection-easy/attempt'
    status,body=request(review_address,'POST',path,json.dumps({'username':True}).encode())
    assert status==422
    status,body=request(review_address,'POST',path,json.dumps({'username':HEAVY}).encode())
    value=json.loads(body)
    assert status==200 and not value['success']
    assert value['learning_trace']['execution']['status']=='resource_limit'
    status,body=request(review_address,'POST',path,json.dumps({'username':"admin' OR 1=1--"}).encode())
    assert status==200 and json.loads(body)['success']


def test_real_http_analysis_uses_compile_only(review_address):
    status,body=request(review_address,'POST','/labs/sql-injection-easy/analyze',json.dumps({'username':HEAVY}).encode())
    value=json.loads(body)
    assert status==200 and value['phase']=='analysis'
    assert value['execution'] is None and value['table'] is None


def test_default_app_does_not_implicitly_enable_unapproved_policy():
    from app.main import app
    payload={'username':'a'*2001}
    assert TestClient(app).post('/labs/sql-injection-easy/analyze',json=payload).status_code==200
    assert client().post('/labs/sql-injection-easy/analyze',json=payload).status_code==422



def test_limit_during_trace_removes_earlier_oracle_success(monkeypatch):
    from app.labs import sql_injection
    original=sql_injection._run_login_query
    oracle_success=[]
    def observed(*args):
        value=original(*args)
        oracle_success.append(value[0])
        return value
    monkeypatch.setattr(sql_injection,'_run_login_query',observed)
    value=client(SQLLimits(640,80,128,8192,32768,32768,8192)).post('/labs/sql-injection-easy/attempt',json={'username':"admin' OR 1=1--"}).json()
    assert oracle_success==[True]
    assert value['success'] is False
    assert value['flow_nodes'] is None
    assert value['learning_trace']['execution']['status']=='resource_limit'



def mounted_client(response_bytes=262144):
    from fastapi import FastAPI
    outer=FastAPI()
    outer.mount('/api',create_review_app(input_limits=INPUT,sql_limits=SQL,sql_authorizer=authorize,response_bytes=response_bytes))
    return TestClient(outer)


def test_mounted_api_does_not_bypass_input_guard():
    r=mounted_client().post('/api/labs/sql-injection-easy/analyze',json={'username':'a'*2001})
    assert r.status_code==422


def test_mounted_api_does_not_bypass_sql_authorizer():
    r=mounted_client().post('/api/labs/sql-injection-easy/attempt',json={'username':"' UNION SELECT 3,sqlite_version(),''--"})
    value=r.json()
    assert not value['success']
    assert value['learning_trace']['execution']['status']=='blocked'


def test_mounted_api_does_not_bypass_response_guard():
    r=mounted_client(1024).get('/api/labs/reflected-xss-easy/render',params={'query':'a'*2000})
    assert r.status_code==503
    assert r.json()['code']=='response_limit'


@pytest.mark.parametrize('path,root,expected',[
    ('/labs/sql-injection-easy/attempt','',True),
    ('/api/labs/sql-injection-easy/attempt','/api',True),
    ('/labs/sql-injection-easy/attempt','/api',True),
    ('/gateway/api/labs/sql-injection-easy/attempt','/gateway/api',True),
    ('/api2/labs/sql-injection-easy/attempt','/api',False),
    ('/api','/api',False),
])
def test_root_path_resolution_matches_exact_segments(path,root,expected):
    from app.core.lab_paths import lab_route
    assert bool(lab_route({'path':path,'root_path':root}))==expected



def test_real_http_mounted_api_enforces_input_sql_and_recovery(review_address):
    path='/api/labs/sql-injection-easy/attempt'
    status,_=request(review_address,'POST',path,json.dumps({'username':'a'*2001}).encode())
    assert status==422
    status,body=request(review_address,'POST',path,json.dumps({'username':"' UNION SELECT 3,sqlite_version(),''--"}).encode())
    value=json.loads(body)
    assert status==200 and not value['success']
    assert value['learning_trace']['execution']['status']=='blocked'
    status,body=request(review_address,'POST',path,json.dumps({'username':"admin' OR 1=1--"}).encode())
    assert status==200 and json.loads(body)['success']


def test_real_http_mounted_api_enforces_response_cap(review_address):
    from urllib.parse import urlencode
    path='/limited-api/labs/reflected-xss-easy/render?'+urlencode({'query':'a'*2000})
    status,body=request(review_address,'GET',path)
    assert status==503 and json.loads(body)['code']=='response_limit'
