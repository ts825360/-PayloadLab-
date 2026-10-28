"""Request-local opt-in wiring; no default numeric or authorizer policy."""
from contextvars import ContextVar
from dataclasses import dataclass
from app.core.lab_paths import lab_route

from app.core.sql_limits import SQLBudget, run_bounded_query


@dataclass
class _RequestSQL:
    limits: object
    authorizer: object
    budget: object = None
    failure: object = None


_active = ContextVar('payloadlab_sql_request', default=None)


def active_sql_failure():
    state = _active.get()
    return state.failure if state else None


def execute_active_sql(query, *, initialize=None, compile_only=False):
    state = _active.get()
    if state is None: return None
    if state.failure is not None: return state.failure
    if state.budget is None: state.budget = SQLBudget(state.limits)
    outcome = run_bounded_query(query, state.limits, state.authorizer,
                                budget=state.budget, initialize=initialize,
                                compile_only=compile_only)
    if outcome.status != 'ok': state.failure = outcome
    return outcome


class SQLScopeMiddleware:
    def __init__(self, app, limits, authorizer):
        self.app, self.limits, self.authorizer = app, limits, authorizer

    async def __call__(self, scope, receive, send):
        match = lab_route(scope) if scope['type'] == 'http' else None
        if not match or scope.get('method') != 'POST' or match[1] not in ('sql-injection-easy','sql-injection-medium') or match[2] not in ('analyze','attempt'):
            return await self.app(scope, receive, send)
        token = _active.set(_RequestSQL(self.limits, self.authorizer))
        try:
            await self.app(scope, receive, send)
        finally:
            _active.reset(token)
