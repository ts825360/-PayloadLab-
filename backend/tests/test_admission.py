"""#44 admission mechanics with injected TEST values, not approved service policy."""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

import pytest

from app.core.admission import (
    AdmissionController, AdmissionPolicy, AdmissionRejected, Rate,
)


class Clock:
    def __init__(self): self.now = 0.0
    def __call__(self): return self.now
    def advance(self, seconds): self.now += seconds


def policy(*, total=20, action=20, peer=20, concurrency=4,
           per_action=4, peers=8, refill=1.0, peer_enabled=True):
    return AdmissionPolicy(
        total_rate=Rate(total, refill),
        action_rates={a: Rate(action, refill) for a in ("analyze", "attempt", "render")},
        peer_rate=Rate(peer, refill) if peer_enabled else None,
        max_active=concurrency,
        action_active={a: per_action for a in ("analyze", "attempt", "render")},
        max_peers=peers,
    )


def accepted(c, action="analyze", peer="192.0.2.1"):
    lease = c.acquire(action, peer)
    lease.release()


def rejected(c, action="analyze", peer="192.0.2.1"):
    with pytest.raises(AdmissionRejected) as exc:
        c.acquire(action, peer)
    return exc.value


def test_burst_boundary_and_release_does_not_refund_frequency():
    c = AdmissionController(policy(total=3), clock=Clock())
    for _ in range(3): accepted(c)
    error = rejected(c)
    assert (error.code, error.status, error.retry_after) == ("rate_limit", 429, 1)
    assert c.snapshot()["active"] == 0


def test_refill_boundary_below_equal_above():
    for elapsed, allow in ((.999, False), (1, True), (1.001, True)):
        clock = Clock()
        c = AdmissionController(policy(total=1), clock=clock)
        accepted(c)
        clock.advance(elapsed)
        if allow: accepted(c)
        else: assert rejected(c).code == "rate_limit"


def test_retry_after_rounds_up_and_uses_slowest_bucket():
    clock = Clock()
    p = policy(total=1, peer=1, refill=.25)
    c = AdmissionController(p, clock=clock)
    accepted(c)
    clock.advance(.1)
    assert rejected(c).retry_after == 4


def test_denied_action_does_not_spend_other_buckets():
    c = AdmissionController(policy(total=2, action=1, peer=2), clock=Clock())
    accepted(c, "analyze")
    assert rejected(c, "analyze").code == "rate_limit"
    accepted(c, "attempt")
    assert rejected(c, "render").code == "rate_limit"


def test_total_is_shared_across_changed_peers_and_actions():
    c = AdmissionController(policy(total=3), clock=Clock())
    for action, ip in zip(("analyze","attempt","render"), ("192.0.2.1","192.0.2.2","192.0.2.3")):
        accepted(c, action, ip)
    assert rejected(c, "attempt", "192.0.2.4").code == "rate_limit"


def test_analysis_bucket_exhaustion_leaves_manual_action_budget():
    c = AdmissionController(policy(total=6, action=2), clock=Clock())
    accepted(c); accepted(c)
    assert rejected(c).code == "rate_limit"
    accepted(c, "attempt")
    accepted(c, "render")


def test_same_ip_can_share_test_allowance_without_being_authentication():
    c = AdmissionController(policy(peer=3), clock=Clock())
    for action in ("analyze","attempt","render"): accepted(c, action)
    assert rejected(c).code == "rate_limit"


def test_ipv6_spellings_and_ipv4_mapped_addresses_share_peer_keys():
    for first, second in [
        ("2001:db8::1", "2001:0db8:0:0:0:0:0:1"),
        ("192.0.2.1", "::ffff:192.0.2.1"),
    ]:
        c = AdmissionController(policy(peer=1), clock=Clock())
        accepted(c, peer=first)
        assert rejected(c, peer=second).code == "rate_limit"


def test_missing_or_invalid_peer_uses_one_bounded_unknown_bucket():
    c = AdmissionController(policy(peer=1), clock=Clock())
    accepted(c, peer=None)
    assert rejected(c, peer="not-an-address").code == "rate_limit"
    assert c.snapshot()["tracked_peers"] == 1


def test_peer_tracking_capacity_is_bounded_and_does_not_reset_old_counters():
    c = AdmissionController(policy(peer=2, peers=2), clock=Clock())
    accepted(c, peer="192.0.2.1")
    accepted(c, peer="192.0.2.2")
    assert rejected(c, peer="192.0.2.3").code == "peer_capacity"
    assert c.snapshot()["tracked_peers"] == 2
    accepted(c, peer="192.0.2.1")
    assert rejected(c, peer="192.0.2.1").code == "rate_limit"


def test_only_fully_refilled_inactive_peer_can_be_reclaimed():
    clock = Clock()
    c = AdmissionController(policy(peer=2, peers=1), clock=clock)
    lease = c.acquire("analyze","192.0.2.1")
    clock.advance(2)
    assert rejected(c, peer="192.0.2.2").code == "peer_capacity"
    lease.release()
    accepted(c, peer="192.0.2.2")
    assert c.snapshot()["tracked_peers"] == 1


def test_not_yet_refilled_peer_cannot_be_evicted_for_new_identity():
    clock = Clock()
    c = AdmissionController(policy(peer=2, peers=1), clock=clock)
    accepted(c)
    clock.advance(.999)
    assert rejected(c, peer="192.0.2.2").code == "peer_capacity"
    clock.advance(.001)
    accepted(c, peer="192.0.2.2")


def test_optional_peer_policy_does_not_track_addresses_but_total_still_holds():
    c = AdmissionController(policy(total=2, peer_enabled=False), clock=Clock())
    accepted(c, peer="192.0.2.1")
    accepted(c, peer="192.0.2.2")
    assert rejected(c, peer="192.0.2.3").code == "rate_limit"
    assert c.snapshot()["tracked_peers"] == 0


def test_active_capacity_rejects_without_queue_or_rate_charge():
    c = AdmissionController(policy(total=2, concurrency=1), clock=Clock())
    lease = c.acquire("analyze","192.0.2.1")
    error = rejected(c, "attempt")
    assert error.code == "concurrency_limit" and error.status == 503
    assert error.retry_after is None  # Completion time is unknown.
    lease.release()
    accepted(c, "attempt")
    assert rejected(c).code == "rate_limit"


def test_action_active_cap_does_not_exhaust_entire_service():
    c = AdmissionController(policy(concurrency=3, per_action=1), clock=Clock())
    first = c.acquire("analyze", "192.0.2.1")
    assert rejected(c).code == "concurrency_limit"
    second = c.acquire("attempt", "192.0.2.2")
    first.release(); second.release()


def test_lease_release_is_idempotent():
    c = AdmissionController(policy(concurrency=1), clock=Clock())
    lease = c.acquire("attempt","192.0.2.1")
    lease.release(); lease.release()
    assert c.snapshot()["active"] == 0
    accepted(c)


def test_parallel_admissions_are_atomic():
    c = AdmissionController(policy(concurrency=2), clock=Clock())
    barrier = threading.Barrier(8)
    release = threading.Event()
    lock = threading.Lock()
    counts = {"accepted":0,"rejected":0}
    def one(i):
        try:
            lease = c.acquire("attempt",f"192.0.2.{i+1}")
        except AdmissionRejected:
            with lock: counts["rejected"] += 1
            barrier.wait(timeout=3)
            return
        with lock: counts["accepted"] += 1
        barrier.wait(timeout=3)
        assert release.wait(3)
        lease.release()
    with ThreadPoolExecutor(max_workers=8) as pool:
        fs=[pool.submit(one,i) for i in range(8)]
        # All 8 competitors reach the barrier; only the 2 winners hold slots.
        for _ in range(300):
            with lock: total = counts["accepted"]+counts["rejected"]
            if total == 8: break
            threading.Event().wait(.001)
        assert c.snapshot()["active"] == 2
        release.set()
        for f in fs: f.result(timeout=5)
    assert counts == {"accepted":2,"rejected":6}
    assert c.snapshot()["active"] == 0


def test_unknown_action_is_rejected_without_state_growth():
    c = AdmissionController(policy(), clock=Clock())
    with pytest.raises(ValueError): c.acquire("unregistered","192.0.2.1")
    assert c.snapshot()["active"] == c.snapshot()["tracked_peers"] == 0


@pytest.mark.parametrize("value", [0,-1,True,float("inf"),float("nan")])
def test_invalid_rate_policy(value):
    with pytest.raises(ValueError): Rate(value, 1)
    with pytest.raises(ValueError): Rate(1, value)


def test_policy_copies_maps_and_requires_matching_actions():
    rates = {"analyze":Rate(2,1)}
    active = {"analyze":1}
    p = AdmissionPolicy(Rate(4,1), rates, None, 2, active, 1)
    rates.clear(); active.clear()
    c = AdmissionController(p, clock=Clock())
    accepted(c)
    with pytest.raises(ValueError):
        AdmissionPolicy(Rate(4,1), {"analyze":Rate(2,1)}, None, 2, {"attempt":1},1)


def test_async_success_and_error_release_slots():
    async def run():
        c = AdmissionController(policy(concurrency=1))
        async def ok(): return 42
        assert await c.run("attempt","192.0.2.1",ok) == 42
        async def bad(): raise RuntimeError("dummy failure")
        with pytest.raises(RuntimeError, match="dummy failure"):
            await c.run("attempt","192.0.2.1",bad)
        await c.wait_idle()
        assert c.snapshot()["active"] == c.snapshot()["owned_tasks"] == 0
    asyncio.run(run())


def test_caller_cancellation_does_not_free_running_async_work_slot():
    async def run():
        c = AdmissionController(policy(concurrency=1))
        entered, release = asyncio.Event(), asyncio.Event()
        async def work():
            entered.set()
            await release.wait()
            return "done"
        caller = asyncio.create_task(c.run("attempt","192.0.2.1",work))
        await entered.wait()
        caller.cancel()
        with pytest.raises(asyncio.CancelledError): await caller
        assert c.snapshot()["active"] == 1
        assert rejected(c).code == "concurrency_limit"
        release.set()
        await c.wait_idle()
        accepted(c)
    asyncio.run(run())


@pytest.mark.parametrize("runner", ["asyncio", "anyio"])
def test_caller_cancellation_keeps_slot_until_sync_thread_actually_finishes(runner):
    async def run():
        c = AdmissionController(policy(concurrency=1))
        entered, release = threading.Event(), threading.Event()
        def sync_work():
            entered.set()
            if not release.wait(3): raise RuntimeError("test release timeout")
        async def work():
            if runner == "anyio":
                import anyio
                await anyio.to_thread.run_sync(sync_work)
            else:
                await asyncio.to_thread(sync_work)
        caller = asyncio.create_task(c.run("attempt","192.0.2.1",work))
        try:
            assert await asyncio.to_thread(entered.wait,2)
            caller.cancel()
            with pytest.raises(asyncio.CancelledError): await caller
            assert c.snapshot()["active"] == 1
            assert rejected(c).code == "concurrency_limit"
        finally:
            release.set()
            await c.wait_idle()
        assert c.snapshot()["active"] == 0
    asyncio.run(run())


def test_rejected_run_does_not_call_handler():
    async def run():
        c = AdmissionController(policy(concurrency=1))
        lease = c.acquire("attempt","192.0.2.1")
        called=[]
        async def work(): called.append(1)
        try:
            with pytest.raises(AdmissionRejected):
                await c.run("attempt","192.0.2.1",work)
        finally: lease.release()
        assert not called
    asyncio.run(run())
def test_retry_after_accounts_for_peer_even_when_total_is_also_empty():
    p = AdmissionPolicy(Rate(1,1), {"analyze":Rate(2,1)}, Rate(1,.25), 2, {"analyze":2},2)
    c = AdmissionController(p, clock=Clock())
    accepted(c)
    assert rejected(c).retry_after == 4


def test_clock_regression_does_not_refill_tokens():
    clock = Clock()
    c = AdmissionController(policy(total=1), clock=clock)
    accepted(c)
    clock.advance(-5)
    assert rejected(c).code == "rate_limit"
    clock.advance(6)
    accepted(c)


def test_cancelled_handler_failure_is_drained_without_raw_error_log(caplog):
    async def run():
        c = AdmissionController(policy(concurrency=1))
        entered, release = asyncio.Event(), asyncio.Event()
        async def work():
            entered.set()
            await release.wait()
            raise RuntimeError("SECRET_DUMMY_INPUT")
        caller=asyncio.create_task(c.run("attempt","192.0.2.1",work))
        await entered.wait()
        caller.cancel()
        with pytest.raises(asyncio.CancelledError): await caller
        release.set()
        await c.wait_idle()
        assert c.snapshot()["active"] == 0
    asyncio.run(run())
    assert "admitted work failed" in caplog.text
    assert "SECRET_DUMMY_INPUT" not in caplog.text