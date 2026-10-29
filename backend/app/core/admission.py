"""Single-process, policy-injected admission primitives for #44.

Not installed in main.app. No production rates, peer trust or queue policy here.
The caller must pass the server-verified peer, never a raw forwarded header.
"""
import asyncio
from dataclasses import dataclass
import ipaddress
import logging
import math
import threading
import time
from types import MappingProxyType
from typing import Mapping

logger = logging.getLogger(__name__)


def _positive_integer(value):
    return type(value) is int and value > 0


@dataclass(frozen=True)
class Rate:
    capacity: int
    per_second: float

    def __post_init__(self):
        if not _positive_integer(self.capacity):
            raise ValueError("capacity must be a positive integer")
        if type(self.per_second) not in (int, float) or not math.isfinite(self.per_second) or self.per_second <= 0:
            raise ValueError("refill must be finite and positive")


@dataclass(frozen=True)
class AdmissionPolicy:
    total_rate: Rate
    action_rates: Mapping[str, Rate]
    peer_rate: Rate | None
    max_active: int
    action_active: Mapping[str, int]
    max_peers: int

    def __post_init__(self):
        rates, active = dict(self.action_rates), dict(self.action_active)
        if not isinstance(self.total_rate, Rate) or (self.peer_rate is not None and not isinstance(self.peer_rate, Rate)):
            raise ValueError("invalid rate policy")
        if not rates or set(rates) != set(active):
            raise ValueError("action budgets must have matching nonempty keys")
        if any(type(k) is not str or not k or not isinstance(v, Rate) for k,v in rates.items()):
            raise ValueError("invalid action rate")
        if not all(_positive_integer(v) for v in [self.max_active, self.max_peers, *active.values()]):
            raise ValueError("active and tracking limits must be positive integers")
        object.__setattr__(self, "action_rates", MappingProxyType(rates))
        object.__setattr__(self, "action_active", MappingProxyType(active))


class AdmissionRejected(Exception):
    def __init__(self, code, status, retry_after=None):
        self.code, self.status, self.retry_after = code, status, retry_after
        # Never reflect a caller's address or payload into an error message.
        super().__init__(code)


@dataclass
class _Bucket:
    rate: Rate
    tokens: float
    updated: float
    active: int = 0

    @classmethod
    def full(cls, rate, now):
        return cls(rate, float(rate.capacity), now)

    def refill(self, now):
        self.tokens = min(float(self.rate.capacity),
                          self.tokens + max(0.0, now-self.updated)*self.rate.per_second)
        self.updated = now

    def wait(self):
        return max(0.0, (1.0-self.tokens)/self.rate.per_second)


def _peer_key(host):
    try:
        value = ipaddress.ip_address(host.split("%",1)[0]) if type(host) is str else None
    except ValueError:
        value = None
    if value is None: return "unknown"
    if isinstance(value, ipaddress.IPv6Address) and value.ipv4_mapped:
        value = value.ipv4_mapped
    return str(value)


class _Lease:
    def __init__(self, owner, action, peer_bucket):
        self._owner, self._action, self._peer = owner, action, peer_bucket
        self._released = False

    def release(self):
        owner = self._owner
        with owner._lock:
            if self._released: return
            self._released = True
            owner._active -= 1
            owner._active_actions[self._action] -= 1
            if self._peer is not None: self._peer.active -= 1


class AdmissionController:
    """Atomic total/action/optional-peer buckets plus a zero-length queue.

    State is process-local, not a multi-worker service-wide limiter.
    For async dispatch use run(): cancellation of its caller does not cancel
    the owned task or return its slot while work is still running.
    """
    def __init__(self, policy, *, clock=time.monotonic):
        if not isinstance(policy, AdmissionPolicy): raise ValueError("invalid admission policy")
        self.policy, self.clock = policy, clock
        self._lock = threading.Lock()
        now = float(clock())
        if not math.isfinite(now): raise ValueError("clock must be finite")
        self._last = now
        self._total = _Bucket.full(policy.total_rate, now)
        self._actions = {k:_Bucket.full(v,now) for k,v in policy.action_rates.items()}
        self._peers = {}
        self._active = 0
        self._active_actions = dict.fromkeys(policy.action_rates, 0)
        self._owned = set()
        self._loop = None

    def _now(self):
        now = float(self.clock())
        if not math.isfinite(now): raise ValueError("clock must be finite")
        self._last = max(now,self._last)
        return self._last

    def acquire(self, action, peer):
        with self._lock:
            if action not in self._actions: raise ValueError("unknown admission action")
            now = self._now()
            # Immediate refusal, no unbounded waiter/task queue.
            if self._active >= self.policy.max_active or self._active_actions[action] >= self.policy.action_active[action]:
                raise AdmissionRejected("concurrency_limit",503)

            buckets = [self._total,self._actions[action]]
            for bucket in buckets: bucket.refill(now)
            peer_bucket, key = None, None
            if self.policy.peer_rate is not None:
                key = _peer_key(peer)
                peer_bucket = self._peers.get(key)
                if peer_bucket is not None:
                    peer_bucket.refill(now)
                    buckets.append(peer_bucket)

            # Consider every existing constraint before calculating Retry-After.
            # A fast-refilling global bucket must not hide a slower peer bucket.
            wait = max(bucket.wait() for bucket in buckets)
            if wait > 0:
                raise AdmissionRejected("rate_limit",429,max(1,math.ceil(wait)))

            if self.policy.peer_rate is not None and peer_bucket is None:
                if len(self._peers) >= self.policy.max_peers:
                    # Never evict depleted or active identities: that would
                    # reset their rate quota while allowing identity churn.
                    expired = []
                    for old_key, old_bucket in self._peers.items():
                        old_bucket.refill(now)
                        if old_bucket.active == 0 and old_bucket.tokens >= old_bucket.rate.capacity:
                            expired.append(old_key)
                    for old_key in expired: del self._peers[old_key]
                if len(self._peers) >= self.policy.max_peers:
                    raise AdmissionRejected("peer_capacity",503)
                peer_bucket = _Bucket.full(self.policy.peer_rate,now)
                buckets.append(peer_bucket)

            # All checks succeeded; charge all buckets and the slot atomically.
            for bucket in buckets: bucket.tokens -= 1
            if peer_bucket is not None:
                self._peers[key] = peer_bucket
                peer_bucket.active += 1
            self._active += 1
            self._active_actions[action] += 1
            return _Lease(self,action,peer_bucket)

    def snapshot(self):
        with self._lock:
            return {"active":self._active,
                    "active_by_action":dict(self._active_actions),
                    "tracked_peers":len(self._peers),
                    "owned_tasks":len(self._owned)}

    async def run(self, action, peer, handler):
        """Run an async callable. Its actual completion owns slot release.

        This is cooperative in-process accounting, not process termination or a
        guarantee against forced loop shutdown / a handler abandoning its own work.
        """
        loop = asyncio.get_running_loop()
        with self._lock:
            if self._loop is not None and self._loop is not loop:
                raise RuntimeError("async dispatch must use one live event loop")
            self._loop = loop
        lease = self.acquire(action,peer)
        abandoned = False
        async def work():
            return await handler()
        coroutine = work()
        try:
            task = loop.create_task(coroutine)
        except BaseException:
            coroutine.close()
            lease.release()
            raise
        with self._lock: self._owned.add(task)

        def finished(done):
            lease.release()
            with self._lock: self._owned.discard(done)
            # Retrieve detached errors; waiting callers still receive the same
            # exception through shield. Log no payload/address/exception detail.
            if not done.cancelled():
                error = done.exception()
                if error is not None and abandoned:
                    logger.error("admitted work failed after caller cancellation")
        task.add_done_callback(finished)
        try:
            return await asyncio.shield(task)
        except asyncio.CancelledError:
            abandoned = True
            raise

    async def wait_idle(self):
        """Graceful drain for tests/lifespan. No fabricated completion timeout."""
        while True:
            with self._lock: tasks = tuple(self._owned)
            if not tasks: return
            await asyncio.gather(*(asyncio.shield(task) for task in tasks), return_exceptions=True)
            # gather may complete synchronously for already-finished tasks.
            # Let their done callbacks release leases/remove owned tasks.
            await asyncio.sleep(0)