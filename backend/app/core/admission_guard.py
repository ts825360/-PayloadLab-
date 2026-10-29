"""Opt-in #44 ASGI adapter. Pass a verified server peer, never raw IP headers."""
import asyncio
import json
from app.core.admission import AdmissionController, AdmissionRejected
from app.core.lab_paths import relative_path, lab_route


def admission_action(scope):
    path = relative_path(scope)
    if path != "/labs" and not path.startswith("/labs/"):
        return None
    match = lab_route(scope)
    if match:
        action = match[2]
        if scope.get("method") == ("GET" if action == "render" else "POST"):
            return action
    return "metadata"


class AdmissionGuard:
    def __init__(self, app, *, controller):
        if not isinstance(controller, AdmissionController):
            raise ValueError("admission controller required")
        if not {"analyze","attempt","render","metadata"} <= set(controller.policy.action_rates):
            raise ValueError("all lab admission actions must be configured")
        self.app, self.controller = app, controller

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope,receive,send)
        action = admission_action(scope)
        if action is None:
            return await self.app(scope,receive,send)
        client = scope.get("client")
        peer = client[0] if client else None
        disconnected, started = False, False
        pending_receives = set()
        pending_sends = set()

        async def tracked_receive():
            nonlocal disconnected
            if disconnected: return {"type":"http.disconnect"}
            # Track transport waits separately: cancelling the owned app task
            # could abandon a still-running sync worker.
            pending = asyncio.ensure_future(receive())
            pending_receives.add(pending)
            try:
                message = await pending
            except asyncio.CancelledError:
                if disconnected: return {"type":"http.disconnect"}
                raise
            finally:
                pending_receives.discard(pending)
            if disconnected or message["type"] == "http.disconnect":
                disconnected = True
                return {"type":"http.disconnect"}
            return message

        async def tracked_send(message):
            nonlocal started
            if disconnected: return
            if message["type"] == "http.response.start": started = True
            pending = asyncio.ensure_future(send(message))
            pending_sends.add(pending)
            try:
                await pending
            except asyncio.CancelledError:
                if not disconnected: raise
            finally:
                pending_sends.discard(pending)

        async def dispatch():
            await self.app(scope,tracked_receive,tracked_send)
        try:
            await self.controller.run(action,peer,dispatch)
        except asyncio.CancelledError:
            disconnected = True
            for pending in tuple(pending_receives | pending_sends):
                pending.cancel()
            raise
        except AdmissionRejected as error:
            if started: raise
            if not disconnected: await self._reject(send,error,action)

    @staticmethod
    async def _reject(send, error, action):
        detail = ("요청이 잠시 몰렸습니다. 잠시 기다린 뒤 다시 시도해 주세요."
                  if error.code == "rate_limit"
                  else "실습 서버가 사용 중입니다. 잠시 후 다시 시도해 주세요.")
        headers = [(b"cache-control",b"no-store"),(b"x-content-type-options",b"nosniff")]
        if error.retry_after is not None:
            headers.append((b"retry-after",str(error.retry_after).encode("ascii")))
        if action == "render":
            wait = f" {error.retry_after}초 뒤 다시 시도해 주세요." if error.retry_after is not None else ""
            body = ('<!doctype html><html lang="ko"><meta charset="utf-8">'
                    '<title>실습 요청 대기</title><p>'+detail+wait+'</p></html>').encode("utf-8")
            content_type = b"text/html; charset=utf-8"
        else:
            payload = {"code":error.code,"detail":detail}
            if error.retry_after is not None: payload["retry_after"] = error.retry_after
            body = json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode("utf-8")
            content_type = b"application/json; charset=utf-8"
        headers += [(b"content-type",content_type),(b"content-length",str(len(body)).encode())]
        await send({"type":"http.response.start","status":error.status,"headers":headers})
        await send({"type":"http.response.body","body":body})