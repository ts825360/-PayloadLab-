"""Explicit policy-injected app for #42 review; main.app remains unchanged."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.request_limits import InputGuard
from app.core.response_limits import ResponseGuard
from app.core.sql_context import SQLScopeMiddleware
from app.routes.labs import router


def create_review_app(*, input_limits, sql_limits, sql_authorizer, response_bytes):
    app = FastAPI(title='PayloadLab policy review app')
    app.include_router(router)
    app.add_middleware(SQLScopeMiddleware, limits=sql_limits, authorizer=sql_authorizer)
    app.add_middleware(InputGuard, limits=input_limits)
    app.add_middleware(ResponseGuard, max_bytes=response_bytes)
    app.add_middleware(CORSMiddleware,
        allow_origins=['http://localhost:5173','http://127.0.0.1:5173'],
        allow_methods=['*'], allow_headers=['*'])
    return app
