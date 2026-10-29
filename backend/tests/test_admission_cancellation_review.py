"""Recheck the cancellation fix at receive/send completion boundaries."""
import asyncio
import pytest

from app.core.admission_guard import AdmissionGuard
from tests.test_admission_http import controller
from tests.test_admission_second_review import scope


def test_cancel_during_blocked_send_finishes_without_late_write():
    async def run():
        c=controller(active=1)
        entered,release=asyncio.Event(),asyncio.Event()
        sent=[]
        async def receive(): return {"type":"http.request","body":b"","more_body":False}
        async def send(message):
            entered.set()
            await release.wait()
            sent.append(message)
        async def endpoint(sc,recv,snd):
            await snd({"type":"http.response.start","status":200,"headers":[]})
            await snd({"type":"http.response.body","body":b"late"})
        caller=asyncio.create_task(AdmissionGuard(endpoint,controller=c)(scope(),receive,send))
        await entered.wait()
        caller.cancel()
        with pytest.raises(asyncio.CancelledError): await caller
        try:
            await asyncio.wait_for(c.wait_idle(),.5)
            assert c.snapshot()["active"]==0 and sent==[]
        finally:
            release.set()
            await c.wait_idle()
    asyncio.run(run())


@pytest.mark.parametrize("body_first",[False,True])
def test_cancel_and_body_arrival_same_loop_turn_does_not_start_processing(body_first):
    async def run():
        c=controller(active=1)
        entered,body_ready=asyncio.Event(),asyncio.Event()
        processed=[]
        async def receive():
            entered.set()
            await body_ready.wait()
            return {"type":"http.request","body":b'{"username":"guest"}',"more_body":False}
        async def send(message): pytest.fail("cancelled scope must not write")
        async def endpoint(sc,recv,snd):
            message=await recv()
            if message["type"]=="http.request": processed.append(message)
        caller=asyncio.create_task(AdmissionGuard(endpoint,controller=c)(scope(),receive,send))
        await entered.wait()
        if body_first: body_ready.set();caller.cancel()
        else: caller.cancel();body_ready.set()
        with pytest.raises(asyncio.CancelledError): await caller
        await asyncio.wait_for(c.wait_idle(),.5)
        assert processed==[] and c.snapshot()["active"]==0
    asyncio.run(run())


@pytest.mark.parametrize("operation",["receive","send"])
def test_unexpected_transport_error_propagates_and_does_not_leak_slot(operation):
    async def run():
        c=controller(active=1)
        sent=[]
        async def receive():
            if operation=="receive": raise OSError("PRIVATE_TRANSPORT_DETAIL")
            return {"type":"http.request","body":b"","more_body":False}
        async def send(message):
            if operation=="send": raise OSError("PRIVATE_TRANSPORT_DETAIL")
            sent.append(message)
        async def endpoint(sc,recv,snd):
            await recv()
            await snd({"type":"http.response.start","status":200,"headers":[]})
        with pytest.raises(OSError,match="PRIVATE_TRANSPORT_DETAIL"):
            await AdmissionGuard(endpoint,controller=c)(scope(),receive,send)
        assert c.snapshot()["active"]==0 and sent==[]
    asyncio.run(run())


def test_repeated_caller_cancel_keeps_receive_cleanup_idempotent():
    async def run():
        c=controller(active=1)
        entered=asyncio.Event()
        async def receive():
            entered.set()
            await asyncio.Future()
        async def send(message): pytest.fail("cancelled scope must not write")
        async def endpoint(sc,recv,snd):
            assert (await recv())["type"]=="http.disconnect"
        caller=asyncio.create_task(AdmissionGuard(endpoint,controller=c)(scope(),receive,send))
        await entered.wait()
        caller.cancel();caller.cancel()
        with pytest.raises(asyncio.CancelledError): await caller
        await asyncio.wait_for(c.wait_idle(),.5)
        assert c.snapshot()["active"]==c.snapshot()["owned_tasks"]==0
    asyncio.run(run())


def test_cancelling_drain_wait_does_not_cancel_admitted_work():
    async def run():
        c=controller(active=1)
        entered,release=asyncio.Event(),asyncio.Event()
        finished=[]
        async def work():
            entered.set()
            await release.wait()
            finished.append(True)
        caller=asyncio.create_task(c.run("attempt","192.0.2.1",work))
        await entered.wait()
        drain=asyncio.create_task(c.wait_idle())
        await asyncio.sleep(0)
        drain.cancel()
        with pytest.raises(asyncio.CancelledError): await drain
        try:
            assert c.snapshot()["active"]==1 and finished==[]
        finally:
            release.set()
            await caller
            await c.wait_idle()
        assert c.snapshot()["active"]==0 and finished==[True]
    asyncio.run(run())