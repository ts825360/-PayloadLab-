"""Injectable SQLite limits for #42; production call sites are not activated.

The caller supplies both numeric policy and an authorizer reviewed by the team.
The VM callback is cooperative; it is not a hard process/OS time boundary.
"""
from dataclasses import dataclass, field
import json
import sqlite3
import time


@dataclass(frozen=True)
class SQLLimits:
    vm_steps: int
    wall_ms: int
    rows: int
    cell_bytes: int
    result_bytes: int
    engine_value_row_bytes: int
    statement_bytes: int

    def __post_init__(self):
        if any(type(v) is not int or v <= 0 for v in vars(self).values()):
            raise ValueError('limits must be positive integers')


@dataclass
class QueryOutcome:
    status: str
    rows: list[tuple] = field(default_factory=list)
    reason: str = ''


class SQLBudget:
    """Conservative shared work budget, not an exact SQLite opcode counter.

    Includes progress intervals, statement reservations and EXPLAIN listing work.
    """
    def __init__(self, limits, clock=time.monotonic):
        self.limits, self.clock = limits, clock
        self.deadline = clock() + limits.wall_ms / 1000
        self.steps = 0
        self.reason = ''

    def expired(self):
        if not self.reason:
            if self.steps >= self.limits.vm_steps: self.reason = 'vm'
            elif self.clock() >= self.deadline: self.reason = 'time'
        return bool(self.reason)

    def reserve_statement(self, statement):
        # SQLite does not call progress for statements shorter than one interval.
        # Charge one interval per statement so their unreported tails cannot reset
        # when trace/resolve open a new connection or use a cached statement.
        self.steps += min(64, self.limits.vm_steps)
        self.expired()

    def progress(self):
        self.steps += min(64, self.limits.vm_steps)
        return int(self.expired())


def run_bounded_query(query, limits, authorizer, *, budget=None, connect=None, initialize=None, compile_only=False):
    budget = budget or SQLBudget(limits)
    if budget.limits != limits: raise ValueError('budget policy mismatch')
    if budget.expired(): return QueryOutcome('resource_limit', reason=budget.reason)
    if type(query) is not str:
        return QueryOutcome('syntax_error', reason='invalid_statement')
    try:
        statement = 'EXPLAIN ' + query if compile_only else query
        if len(statement.encode('utf-8')) > limits.statement_bytes:
            return QueryOutcome('resource_limit', reason='statement_bytes')
    except (AttributeError, UnicodeError):
        return QueryOutcome('syntax_error', reason='invalid_statement')
    conn = cursor = None
    denied = False
    def authorize(*args):
        nonlocal denied
        try:
            result = authorizer(*args)
        except Exception:
            denied = True
            return sqlite3.SQLITE_DENY
        if result != sqlite3.SQLITE_OK:
            # IGNORE can substitute NULL for a column: do not call that an
            # unchanged successful educational query result.
            denied = True
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    try:
        conn = connect() if connect else sqlite3.connect(':memory:')
        conn.set_progress_handler(budget.progress, min(64, limits.vm_steps))
        conn.set_trace_callback(budget.reserve_statement)
        conn.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, limits.statement_bytes)
        conn.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, limits.engine_value_row_bytes)
        # Initializer is trusted seed code, not user SQL. Its work shares the budget.
        if initialize: initialize(conn)
        conn.set_authorizer(authorize)
        if compile_only:
            # EXPLAIN can bypass SQLite's usual trace/progress notifications.
            # Reserve preparation work explicitly rather than relying on them.
            budget.reserve_statement(statement)
        if budget.expired(): return QueryOutcome('resource_limit', reason=budget.reason)
        cursor = conn.execute(statement)
        rows = []
        encoded_bytes = 2  # JSON list brackets.
        for row in cursor:
            if budget.expired(): return QueryOutcome('resource_limit', reason=budget.reason)
            if compile_only:
                # Charge each listed instruction as analysis work, not an
                # executed VM instruction or a returned account row.
                budget.steps += 1
                if budget.expired():
                    return QueryOutcome('resource_limit', reason=budget.reason)
                continue
            if len(rows) >= limits.rows:
                return QueryOutcome('resource_limit', reason='rows')
            for value in row:
                if type(value) not in (str, int, float, type(None)):
                    return QueryOutcome('blocked', reason='unsupported_result')
                if isinstance(value, str) and len(value.encode('utf-8')) > limits.cell_bytes:
                    return QueryOutcome('resource_limit', reason='cell_bytes')
            try:
                encoded = json.dumps(row, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
            except (ValueError, UnicodeError):
                return QueryOutcome('blocked', reason='unsupported_result')
            encoded_bytes += len(encoded) + int(bool(rows))
            if encoded_bytes > limits.result_bytes:
                return QueryOutcome('resource_limit', reason='result_bytes')
            rows.append(row)
        if budget.expired(): return QueryOutcome('resource_limit', reason=budget.reason)
        return QueryOutcome('ok', rows)
    except sqlite3.Error as exc:
        if budget.expired(): return QueryOutcome('resource_limit', reason=budget.reason)
        if denied: return QueryOutcome('blocked', reason='operation')
        if getattr(exc, 'sqlite_errorcode', None) == sqlite3.SQLITE_TOOBIG:
            return QueryOutcome('resource_limit', reason='engine_value_or_statement')
        # Do not reflect arbitrary SQLite exception text, file paths or user input.
        return QueryOutcome('syntax_error', reason='invalid_statement')
    finally:
        try:
            if cursor is not None: cursor.close()
        finally:
            if conn is not None:
                try:
                    conn.set_progress_handler(None, 0)
                    conn.set_authorizer(None)
                    conn.set_trace_callback(None)
                finally:
                    conn.close()
