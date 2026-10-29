"""#44 actual loopback HTTP, with injected TEST policy and no upstream proxy trust."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import http.client
import json
import os
from pathlib import Path
import socket
import threading
import time
from urllib.parse import urlencode

import pytest
import uvicorn
from fastapi import FastAPI

from app.core.admission import AdmissionController, AdmissionPolicy, Rate
from app.core.admission_guard import AdmissionGuard, admission_action
from app.review_app import create_review_app, local_review_config
from tests.test_admission import Clock
from tests.test_request_limits import LIMITS as INPUT
from tests.test_review_app import SQL
from tests.test_sql_limits import authorize

OBSERVATIONS=[]


@pytest.fixture(scope="module", autouse=True)
def record_http_observations():
    yield
    destination=os.environ.get("ISSUE44_HTTP_EVIDENCE")
    if destination:
        Path(destination).write_text(json.dumps({
            "scope":"controlled loopback HTTP; TEST policy; single process; no public targets",
            "count":len(OBSERVATIONS),"requests":OBSERVATIONS,
        },ensure_ascii=False,indent=2)+"\n",encoding="utf-8")


def controller(total=20, action=20, peer=None, active=4, clock=None):
    return AdmissionController(AdmissionPolicy(
        Rate(total,1),
        {k:Rate(action,1) for k in ("analyze","attempt","render","metadata")},
        Rate(peer,1) if peer else None,
        active,{k:active for k in ("analyze","attempt","render","metadata")},8,
    ),clock=clock or Clock())


@contextmanager
def server(c, slow=False):
    app=create_review_app(input_limits=INPUT,sql_limits=SQL,
        sql_authorizer=authorize,response_bytes=262144,admission_controller=c)
    entered,release=threading.Event(),threading.Event()
    if slow:
        @app.post("/labs/probe/attempt")
        def probe(payload:dict):
            entered.set()
            if not release.wait(4): raise RuntimeError("probe release timeout")
            return {"ok":True}
        # Probe must precede the real /labs/{lab_id}/attempt route.
        app.router.routes.insert(0,app.router.routes.pop())
    outer=FastAPI()
    outer.mount("/api",app)
    outer.mount("/",app)
    sock=socket.socket()
    sock.bind(("127.0.0.1",0))
    address=sock.getsockname()
    config=local_review_config(outer,port=address[1])
    assert config.proxy_headers is False and config.workers==1
    runner=uvicorn.Server(config)
    thread=threading.Thread(target=runner.run,kwargs={"sockets":[sock]},daemon=True)
    thread.start()
    try:
        end=time.monotonic()+5
        while not runner.started:
            if not thread.is_alive() or time.monotonic()>end:
                raise RuntimeError("review test server did not start")
            time.sleep(.01)
        yield address,entered,release
    finally:
        release.set()
        runner.should_exit=True
        thread.join(5)
        sock.close()
        assert not thread.is_alive(),"review test server did not stop"


def request(address,path="/labs/sql-injection-easy/analyze",payload=None,headers=None,method="POST"):
    body=json.dumps({"username":"guest"} if payload is None else payload).encode() if method=="POST" else None
    conn=http.client.HTTPConnection(*address,timeout=5)
    try:
        conn.request(method,path,body,{"Content-Type":"application/json",**(headers or {})})
        result=conn.getresponse()
        raw=result.read()
        item={"method":method,"path":path,"status":result.status,
              "retry_after":result.getheader("Retry-After"),"bytes":len(raw)}
        OBSERVATIONS.append(item)
        return result.status,dict((k.lower(),v) for k,v in result.getheaders()),raw
    finally: conn.close()


def test_real_http_burst_boundary_retry_and_recovery():
    clock=Clock();c=controller(total=2,clock=clock)
    with server(c) as (address,_,__):
        assert request(address)[0]==200
        assert request(address)[0]==200
        status,headers,raw=request(address)
        assert status==429 and headers["retry-after"]=="1"
        assert json.loads(raw)["code"]=="rate_limit"
        assert headers["cache-control"]=="no-store"
        clock.advance(1)
        assert request(address)[0]==200


def test_direct_and_mounted_paths_share_one_total():
    c=controller(total=2)
    with server(c) as (address,_,__):
        assert request(address)[0]==200
        assert request(address,"/api/labs/sql-injection-easy/attempt")[0]==200
        assert request(address,"/labs/reflected-xss-easy/render?query=hello",method="GET")[0]==429


def test_changing_forwarded_headers_cannot_reset_peer_allowance():
    c=controller(peer=2)
    with server(c) as (address,_,__):
        for n in (10,11):
            assert request(address,headers={"X-Forwarded-For":f"198.51.100.{n}","Forwarded":f"for=198.51.100.{n}"})[0]==200
        assert request(address,headers={"X-Forwarded-For":"203.0.113.10"})[0]==429
        assert c.snapshot()["tracked_peers"]==1


def test_small_same_peer_allowance_preserves_three_normal_requests():
    c=controller(peer=3)
    with server(c) as (address,_,__):
        for action in ("analyze","attempt"):
            assert request(address,f"/labs/sql-injection-easy/{action}")[0]==200
        assert request(address,"/labs/reflected-xss-easy/render?query=hello",method="GET")[0]==200
        assert request(address)[0]==429


def test_analysis_limit_does_not_spend_remaining_attempt_bucket():
    c=controller(total=5,action=1)
    with server(c) as (address,_,__):
        assert request(address)[0]==200
        assert request(address)[0]==429
        assert request(address,"/labs/sql-injection-easy/attempt")[0]==200


def test_render_rejection_is_fixed_html_not_reflected_payload():
    c=controller(total=1)
    path="/labs/reflected-xss-easy/render?"+urlencode({"query":"<script>SECRET_DUMMY</script>"})
    with server(c) as (address,_,__):
        assert request(address)[0]==200
        status,headers,body=request(address,path,method="GET")
        assert status==429 and "text/html" in headers["content-type"]
        assert b"<script>" not in body and b"SECRET_DUMMY" not in body
        assert "잠시".encode() in body and headers["retry-after"]=="1"


def test_metadata_and_invalid_methods_count_but_health_remains_separate():
    c=controller(total=2)
    with server(c) as (address,_,__):
        assert request(address,"/labs",method="GET")[0]==200
        assert request(address,"/labs/sql-injection-easy/analyze",method="GET")[0]==405
        assert request(address,"/labs/missing",method="GET")[0]==429
        assert request(address,"/health",method="GET")[0]==404  # Review app has no health route; it is not rate-limited.


def test_cors_error_exposes_retry_after_and_does_not_spend_preflight():
    c=controller(total=1)
    headers={"Origin":"http://127.0.0.1:5173"}
    with server(c) as (address,_,__):
        assert request(address,headers={**headers,"Access-Control-Request-Method":"POST"},method="OPTIONS")[0]==200
        assert request(address,headers=headers)[0]==200
        status,h,body=request(address,headers=headers)
        assert status==429
        assert h["access-control-allow-origin"]==headers["Origin"]
        assert "Retry-After" in h["access-control-expose-headers"]


def test_concurrent_http_rejection_and_recovery():
    c=controller(active=1)
    with server(c,slow=True) as (address,entered,release):
        with ThreadPoolExecutor(max_workers=1) as pool:
            first=pool.submit(request,address,"/labs/probe/attempt",{})
            try:
                assert entered.wait(2)
                status,headers,raw=request(address)
                assert status==503 and json.loads(raw)["code"]=="concurrency_limit"
                assert "retry-after" not in headers  # Work completion time is unknown.
                assert c.snapshot()["active"]==1
            finally: release.set()
            assert first.result(timeout=3)[0]==200
        assert request(address)[0]==200


def test_disconnected_http_keeps_slot_until_sync_handler_finishes():
    c=controller(active=1)
    with server(c,slow=True) as (address,entered,release):
        conn=http.client.HTTPConnection(*address,timeout=3)
        try:
            conn.request("POST","/labs/probe/attempt",b"{}",{"Content-Type":"application/json"})
            assert entered.wait(2)
        finally: conn.close()
        OBSERVATIONS.append({"method":"POST","path":"/labs/probe/attempt","status":None,"outcome":"client closed without reading a response"})
        assert request(address)[0]==503
        assert c.snapshot()["active"]==1
        release.set()
        end=time.monotonic()+2
        while c.snapshot()["active"] and time.monotonic()<end: time.sleep(.005)
        assert request(address)[0]==200


@pytest.mark.parametrize("path,root,method,expected",[
    ("/labs/sql-injection-easy/analyze","","POST","analyze"),
    ("/api/labs/sql-injection-easy/attempt","/api","POST","attempt"),
    ("/labs/reflected-xss-easy/render","/api","GET","render"),
    ("/gateway/api/labs","/gateway/api","GET","metadata"),
    ("/api2/labs/sql-injection-easy/attempt","/api","POST",None),
    ("/health","","GET",None),
    ("/labs/sql-injection-easy/analyze","","GET","metadata"),
])
def test_exact_route_classification(path,root,method,expected):
    assert admission_action({"path":path,"root_path":root,"method":method})==expected


def test_changed_controlled_asgi_peer_still_shares_total_budget():
    async def run():
        c=controller(total=2)
        async def endpoint(scope,receive,send):
            await send({"type":"http.response.start","status":200,"headers":[]})
            await send({"type":"http.response.body","body":b"ok"})
        app=AdmissionGuard(endpoint,controller=c)
        statuses=[]
        for ip in ("192.0.2.1","192.0.2.2","192.0.2.3"):
            sent=[]
            async def receive(): return {"type":"http.request","body":b"","more_body":False}
            async def send(message): sent.append(message)
            await app({"type":"http","path":"/labs/a/analyze","method":"POST","client":(ip,1)},receive,send)
            statuses.append(sent[0]["status"])
        assert statuses==[200,200,429]
    asyncio.run(run())


def test_cancelled_asgi_caller_drops_late_sends_and_holds_slot():
    async def run():
        c=controller(active=1)
        entered,release=asyncio.Event(),asyncio.Event()
        async def endpoint(scope,receive,send):
            entered.set()
            await release.wait()
            await send({"type":"http.response.start","status":200,"headers":[]})
            await send({"type":"http.response.body","body":b"late"})
        app=AdmissionGuard(endpoint,controller=c)
        sent=[]
        async def receive(): return {"type":"http.request","body":b"","more_body":False}
        async def send(message): sent.append(message)
        scope={"type":"http","path":"/labs/a/attempt","method":"POST","client":("192.0.2.1",1)}
        caller=asyncio.create_task(app(scope,receive,send))
        await entered.wait()
        caller.cancel()
        with pytest.raises(asyncio.CancelledError): await caller
        assert c.snapshot()["active"]==1
        release.set()
        await c.wait_idle()
        assert c.snapshot()["active"]==0 and sent==[]
    asyncio.run(run())
@pytest.mark.parametrize("path,expected",[
    ("/labs/sql-injection-easy/analyze/",307),
    ("/api/labs/sql-injection-easy/analyze/",307),
    ("/labs/%73ql-injection-easy/analyze",200),
    ("/api/labs/%73ql-injection-easy/analyze",200),
])
def test_alias_paths_cannot_bypass_shared_total(path,expected):
    c=controller(total=1)
    with server(c) as (address,_,__):
        assert request(address,path)[0]==expected
        assert request(address)[0]==429


def test_rejected_input_also_uses_admission_budget_then_normal_request_recovers():
    c=controller(total=2)
    with server(c) as (address,_,__):
        assert request(address,payload={"username":True})[0]==422
        assert request(address)[0]==200
        assert request(address)[0]==429


def test_head_limit_has_no_response_body_and_keeps_status():
    c=controller(total=1)
    with server(c) as (address,_,__):
        assert request(address)[0]==200
        status,headers,body=request(address,"/labs",method="HEAD")
        assert status==429 and body==b""


def test_same_keepalive_connection_recovers_after_rejected_unread_request_body():
    clock=Clock();c=controller(total=1,clock=clock)
    with server(c) as (address,_,__):
        conn=http.client.HTTPConnection(*address,timeout=3)
        def exchange(payload):
            conn.request("POST","/labs/sql-injection-easy/analyze",
                json.dumps(payload).encode(),{"Content-Type":"application/json"})
            response=conn.getresponse()
            raw=response.read()
            OBSERVATIONS.append({"method":"POST","path":"/labs/sql-injection-easy/analyze",
                "status":response.status,"bytes":len(raw),"kind":"same keepalive connection"})
            return response.status
        try:
            assert exchange({"username":"guest"})==200
            assert exchange({"username":"a"*64})==429
            clock.advance(1)
            assert exchange({"username":"guest"})==200
        finally: conn.close()