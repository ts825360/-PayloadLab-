"""Explicit policy-injected app for #42 review; main.app remains unchanged."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.request_limits import InputGuard
from app.core.response_limits import ResponseGuard
from app.core.sql_context import SQLScopeMiddleware
from app.core.admission_guard import AdmissionGuard
from app.routes.labs import router


def create_review_app(*, input_limits, sql_limits, sql_authorizer, response_bytes,
                      admission_controller=None):
    @asynccontextmanager
    async def lifespan(app):
        try:
            yield
        finally:
            if admission_controller is not None:
                await admission_controller.wait_idle()

    app = FastAPI(title='PayloadLab policy review app', lifespan=lifespan)
    app.include_router(router)
    app.add_middleware(SQLScopeMiddleware, limits=sql_limits, authorizer=sql_authorizer)
    app.add_middleware(InputGuard, limits=input_limits)
    app.add_middleware(ResponseGuard, max_bytes=response_bytes)
    if admission_controller is not None:
        app.add_middleware(AdmissionGuard, controller=admission_controller)
    app.add_middleware(CORSMiddleware,
        allow_origins=['http://localhost:5173','http://127.0.0.1:5173'],
        allow_methods=['*'], allow_headers=['*'], expose_headers=['Retry-After'])
    return app


def local_review_config(app, *, port):
    """Single-process loopback review; never trust forwarded IP headers."""
    import uvicorn
    if type(port) is not int or not 1 <= port <= 65535:
        raise ValueError("valid loopback review port required")
    return uvicorn.Config(app, host="127.0.0.1", port=port, workers=1,
        proxy_headers=False, forwarded_allow_ips="", reload=False,
        log_level="error", access_log=False, ws="none")
