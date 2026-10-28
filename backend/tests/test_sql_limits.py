"""Controlled SQLite mechanism tests with injected unapproved #42 policy."""
import sqlite3

import pytest
from app.labs import sql_injection as lesson_sql

from app.core.sql_limits import SQLLimits, SQLBudget, run_bounded_query

LIMITS = SQLLimits(8192, 80, 128, 8192, 32768, 32768, 8192)


def authorize(action, arg1, arg2, database, trigger):
    if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_RECURSIVE): return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_FUNCTION and arg2 in {'length', 'printf', 'sum'}: return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def run(query, limits=LIMITS, budget=None, factory=None):
    return run_bounded_query(query, limits, authorize, budget=budget, **({'connect': factory} if factory else {}))


def test_normal_select_union_and_comment():
    result = run('SELECT 1, 2, 3 UNION ALL SELECT 4,5,6 -- lesson')
    assert result.status == 'ok'
    assert result.rows == [(1,2,3), (4,5,6)]


def test_vm_budget_interrupts_and_new_request_recovers():
    result = run('WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n WHERE x<10000) SELECT sum(x) FROM n')
    assert result.status == 'resource_limit'
    assert result.reason == 'vm'
    assert result.rows == []
    assert run('SELECT 1').rows == [(1,)]


def test_shared_budget_is_not_reset_between_trace_and_resolve():
    limits = SQLLimits(64, 80, 128, 8192, 32768, 32768, 8192)
    budget = SQLBudget(limits)
    query='WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n WHERE x<100) SELECT sum(x) FROM n'
    assert run(query, limits, budget).reason == 'vm'
    assert run('SELECT 1', limits, budget).reason == 'vm'


def test_deadline_can_expire_before_execute():
    budget = SQLBudget(LIMITS, clock=lambda: 0)
    budget.clock = lambda: 1
    assert run('SELECT 1', budget=budget).reason == 'time'


def test_row_limit_below_at_above():
    for n in (127, 128, 129):
        query=f'WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n WHERE x<{n}) SELECT x FROM n'
        result=run(query)
        assert result.status == ('resource_limit' if n>128 else 'ok')
        assert len(result.rows) == (0 if n>128 else n)


def test_cell_byte_limit_includes_unicode():
    for n in (2047, 2048, 2049):
        result=run("SELECT '"+'😀'*n+"'", SQLLimits(8192,80,128,8192,32768,32768,16384))
        assert result.status == ('resource_limit' if n>2048 else 'ok')


def test_total_result_cap_is_separate_from_single_cell():
    query="WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n WHERE x<10) SELECT printf('%4000s','a') FROM n"
    result=run(query)
    assert result.status=='resource_limit'
    assert result.reason=='result_bytes'
    assert result.rows==[]


def test_authorizer_blocks_attach_and_extension_without_opening_files():
    for query in ("ATTACH DATABASE '/not-a-real-location/private.db' AS other", "SELECT load_extension('/private/plugin')", 'PRAGMA database_list', 'CREATE TABLE x(y)'):
        result=run(query)
        assert result.status=='blocked'
        assert '/private' not in result.reason
        assert '/not-a-real-location' not in result.reason


def test_connection_is_closed_on_success_syntax_and_interruption():
    for query in ('SELECT 1', 'SELECT broken syntax', 'WITH RECURSIVE n(x) AS (VALUES(1) UNION ALL SELECT x+1 FROM n WHERE x<10000) SELECT sum(x) FROM n'):
        connections=[]
        def factory():
            c=sqlite3.connect(':memory:'); connections.append(c); return c
        run(query, factory=factory)
        try: connections[0].execute('SELECT 1')
        except sqlite3.ProgrammingError: pass
        else: raise AssertionError('connection leaked')


def test_syntax_error_does_not_expose_input_or_paths():
    result=run("SELECT * FROM '/private/table'")
    assert result.status=='syntax_error'
    assert '/private' not in result.reason


def test_result_serialized_bytes_below_at_above():
    limits=SQLLimits(8192,80,128,8192,12,32768,8192)
    for count in (5,6,7):
        result=run("SELECT '"+'a'*count+"'",limits)
        assert result.status==('resource_limit' if count==7 else 'ok')


def test_statement_bytes_below_at_above():
    limits=SQLLimits(8192,80,128,8192,32768,32768,10)
    for count in (9,10,11):
        result=run('SELECT 1'+' '*(count-8),limits)
        assert result.status==('resource_limit' if count==11 else 'ok')


def test_blob_and_non_finite_are_controlled_results():
    for query in ("SELECT x'1234'",'SELECT 1e999'):
        assert run(query).reason=='unsupported_result'


def test_many_short_queries_cannot_skip_shared_vm_accounting():
    limits=SQLLimits(256,1000,128,8192,32768,32768,8192)
    budget=SQLBudget(limits)
    results=[run('SELECT 1',limits,budget) for _ in range(60)]
    assert any(r.reason=='vm' for r in results)
    first_limit=next(i for i,r in enumerate(results) if r.reason=='vm')
    assert all(r.reason=='vm' for r in results[first_limit:])


def test_authorizer_ignore_cannot_silently_return_modified_rows():
    def seed(c):
        c.execute('CREATE TABLE users(username TEXT)')
        c.execute("INSERT INTO users VALUES('admin')")
    def ignore_read(action,*args):
        return sqlite3.SQLITE_IGNORE if action==sqlite3.SQLITE_READ else sqlite3.SQLITE_OK
    result=run_bounded_query('SELECT username FROM users',LIMITS,ignore_read,initialize=seed)
    assert result.status=='blocked'
    assert result.rows==[]


def test_authorizer_failure_is_a_controlled_block_not_syntax_error():
    def broken(*args): raise RuntimeError('/private/policy.py')
    result=run_bounded_query('SELECT 1',LIMITS,broken)
    assert result.status=='blocked'
    assert '/private' not in result.reason


@pytest.mark.parametrize('raw,medium,expected_status', [
    ('박태성',False,'ok'),
    ('',False,'ok'),
    ("admin' OR '1'='1'--",False,'ok'),
    ("admin' OR '1'='1'--",True,'syntax_error'),
    ("admin' oR '1'='1'--",True,'ok'),
    ("' UNION ALL SELECT 3,'learner','dummy'--",False,'ok'),
])
def test_bounded_executor_preserves_existing_educational_query_rows(raw,medium,expected_status):
    filter_fn=lesson_sql._strip_uppercase_or if medium else lesson_sql._identity_filter
    expected=lesson_sql._run_login_query(raw,filter_fn)[2]
    def seed(c):
        c.execute('CREATE TABLE users(id INTEGER PRIMARY KEY,username TEXT,password TEXT)')
        c.executemany('INSERT INTO users VALUES(?,?,?)',lesson_sql._SEED_USERS)
        c.commit()
    result=run_bounded_query(lesson_sql.compose_query(filter_fn(raw)),LIMITS,authorize,initialize=seed)
    assert result.status==expected_status
    assert result.rows==expected



def test_compile_only_does_not_apply_returned_data_row_limit_to_bytecode():
    query=' UNION ALL '.join('SELECT '+str(i) for i in range(83))
    compiled=run_bounded_query(query,LIMITS,authorize,compile_only=True)
    assert compiled.status=='ok'
    assert compiled.rows==[]
    assert len(run(query).rows)==83


def test_compile_only_does_not_execute_user_sql_function():
    calls=[]
    def setup(c): c.create_function('marker',0,lambda: calls.append(True) or 7)
    def allow_marker(action,arg1,arg2,*args):
        if action==sqlite3.SQLITE_FUNCTION and arg2=='marker': return sqlite3.SQLITE_OK
        return authorize(action,arg1,arg2,*args)
    result=run_bounded_query('SELECT marker()',LIMITS,allow_marker,initialize=setup,compile_only=True)
    assert result.status=='ok' and result.rows==[]
    assert calls==[]


def test_compile_only_still_rejects_disallowed_operations():
    result=run_bounded_query('DROP TABLE users',LIMITS,authorize,compile_only=True,initialize=lambda c:c.execute('CREATE TABLE users(id INTEGER)'))
    assert result.status=='blocked'



def test_repeated_explain_does_not_skip_shared_budget():
    limits=SQLLimits(256,1000,128,8192,32768,32768,8192)
    budget=SQLBudget(limits)
    results=[run_bounded_query('SELECT 1',limits,authorize,budget=budget,compile_only=True) for _ in range(60)]
    assert any(r.reason=='vm' for r in results)
    assert all(r.rows==[] for r in results)


def test_explain_instruction_listing_is_charged_to_analysis_budget():
    limits=SQLLimits(128,1000,128,8192,32768,32768,8192)
    query=' UNION ALL '.join('SELECT '+str(i) for i in range(83))
    result=run_bounded_query(query,limits,authorize,compile_only=True)
    assert result.status=='resource_limit' and result.reason=='vm'
    assert result.rows==[]
