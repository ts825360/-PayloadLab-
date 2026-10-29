"""#44 second review: lifecycle, receive cancellation and error boundaries."""
import asyncio

import pytest

from app.core.admission_guard import AdmissionGuard
from app.review_app import create_review_app
from tests.test_admission_http import controller
from tests.test_request_limits import LIMITS as INPUT
from tests.test_review_app import SQL
from tests.test_sql_limits import authorize


def scope():
    return {"type":"http","path":"/labs/probe/attempt","method":"POST",
            "client":("192.0.2.1",1)}


def test_cancel_during_body_receive_does_not_leave_a_slot_waiting_forever():
    async def run():
        c=controller(active=1)
        entered, allow_receive=asyncio.Event(),asyncio.Event()
        sent=[]
        async def receive():
            entered.set()
            await allow_receive.wait()
            return {"type":"http.disconnect"}
        async def send(message): sent.append(message)
        async def endpoint(sc,recv,snd):
            message=await recv()
            assert message["type"]=="http.disconnect"
        app=AdmissionGuard(endpoint,controller=c)
        caller=asyncio.create_task(app(scope(),receive,send))
        await entered.wait()
        caller.cancel()
        with pytest.raises(asyncio.CancelledError): await caller
        try:
            # Test watchdog only, not a proposed production request timeout.
            await asyncio.wait_for(c.wait_idle(),.5)
            assert c.snapshot()["active"]==0 and sent==[]
        finally:
            allow_receive.set()
            await c.wait_idle()
    asyncio.run(run())


def test_observed_disconnect_drops_downstream_late_sends_and_releases():
    async def run():
        c=controller(active=1)
        sent=[]
        async def receive(): return {"type":"http.disconnect"}
        async def send(message): sent.append(message)
        async def endpoint(sc,recv,snd):
            assert (await recv())["type"]=="http.disconnect"
            await snd({"type":"http.response.start","status":200,"headers":[]})
            await snd({"type":"http.response.body","body":b"late"})
        await AdmissionGuard(endpoint,controller=c)(scope(),receive,send)
        assert sent==[] and c.snapshot()["active"]==0
    asyncio.run(run())


@pytest.mark.parametrize("start_first",[False,True])
def test_unexpected_error_propagates_without_fabricating_another_response(start_first):
    async def run():
        c=controller(active=1)
        sent=[]
        async def receive(): return {"type":"http.request","body":b"","more_body":False}
        async def send(message): sent.append(message)
        async def endpoint(sc,recv,snd):
            if start_first:
                await snd({"type":"http.response.start","status":200,"headers":[]})
            raise RuntimeError("CONTROLLED_PRIVATE_DETAIL")
        app=AdmissionGuard(endpoint,controller=c)
        with pytest.raises(RuntimeError,match="CONTROLLED_PRIVATE_DETAIL"):
            await app(scope(),receive,send)
        assert len(sent)==int(start_first)
        assert c.snapshot()["active"]==0
        async def normal(sc,recv,snd):
            await snd({"type":"http.response.start","status":200,"headers":[]})
            await snd({"type":"http.response.body","body":b"ok"})
        await AdmissionGuard(normal,controller=c)(scope(),receive,send)
        assert sent[-1]["body"]==b"ok"
    asyncio.run(run())


def test_review_app_shutdown_waits_for_actual_admitted_work_completion():
    async def run():
        c=controller(active=1)
        app=create_review_app(input_limits=INPUT,sql_limits=SQL,
            sql_authorizer=authorize,response_bytes=262144,admission_controller=c)
        entered,release=asyncio.Event(),asyncio.Event()
        async def work():
            entered.set()
            await release.wait()
        lifetime=app.router.lifespan_context(app)
        await lifetime.__aenter__()
        caller=asyncio.create_task(c.run("attempt","192.0.2.1",work))
        await entered.wait()
        shutdown=asyncio.create_task(lifetime.__aexit__(None,None,None))
        await asyncio.sleep(0)
        try:
            assert not shutdown.done() and c.snapshot()["active"]==1
        finally:
            release.set()
            await caller
            await shutdown
        assert c.snapshot()["active"]==c.snapshot()["owned_tasks"]==0
    asyncio.run(run())

def test_review_pipeline_cancel_during_body_does_not_run_model(monkeypatch):
    from app.routes import labs as routes
    called=[]
    monkeypatch.setattr(routes,"build_input_analysis",lambda *args: called.append(args) or {})
    async def run():
        c=controller(active=1)
        app=create_review_app(input_limits=INPUT,sql_limits=SQL,
            sql_authorizer=authorize,response_bytes=262144,admission_controller=c)
        entered,allow_receive=asyncio.Event(),asyncio.Event()
        sent=[]
        async def receive():
            entered.set()
            await allow_receive.wait()
            return {"type":"http.disconnect"}
        async def send(message): sent.append(message)
        sc={"type":"http","asgi":{"version":"3.0"},"http_version":"1.1",
            "method":"POST","scheme":"http","path":"/labs/sql-injection-easy/analyze",
            "raw_path":b"/labs/sql-injection-easy/analyze","root_path":"",
            "query_string":b"","headers":[(b"content-type",b"application/json")],
            "server":("test",80),"client":("192.0.2.1",1)}
        caller=asyncio.create_task(app(sc,receive,send))
        await entered.wait()
        caller.cancel()
        with pytest.raises(asyncio.CancelledError): await caller
        try:
            await asyncio.wait_for(c.wait_idle(),.5)
            assert c.snapshot()["active"]==0 and called==[] and sent==[]
        finally:
            allow_receive.set()
            await c.wait_idle()
    asyncio.run(run())