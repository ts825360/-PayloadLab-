"""New bounded helper vs frozen sizing corpus; test simulation, not live wiring."""
import json
from pathlib import Path
import platform
import sqlite3
import sys
import time

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'backend'))
from app.core.sql_limits import SQLLimits,SQLBudget,run_bounded_query
from app.labs import sql_injection as sql

LIMITS=SQLLimits(8192,80,128,8192,32768,32768,8192)
def authorize(action,*args):
    return sqlite3.SQLITE_OK if action in (sqlite3.SQLITE_READ,sqlite3.SQLITE_SELECT) else sqlite3.SQLITE_DENY

def seed(c):
    c.execute('CREATE TABLE users(id INTEGER PRIMARY KEY,username TEXT,password TEXT)')
    c.executemany('INSERT INTO users VALUES(?,?,?)',sql._SEED_USERS)
    c.commit()

def baseline(query,analysis=False):
    c=sql._seed_db()
    started=time.monotonic();steps=[0]
    def guard():
        steps[0]+=100
        return int(steps[0]>=100000 or time.monotonic()-started>.05)
    c.set_progress_handler(guard,100)
    try:
        rows=c.execute(('EXPLAIN ' if analysis else '')+query).fetchall()
        return 'ok',[] if analysis else rows
    except sqlite3.Error:
        return 'syntax_error',[]
    finally:c.close()

source=ROOT/'docs/verification/evidence/2026-10-28-issue42-sizing.json'
corpus=json.loads(source.read_text(encoding='utf-8'))
payloads={}
for version in corpus['versions']:
    for rec in version['records']:
        if rec['lab'].startswith('sql-injection-'):
            raw=rec['payload'].get('username')
            if isinstance(raw,str):payloads[(rec['lab'],raw)]=rec['source']
records=[]
for (lab,raw),source_name in sorted(payloads.items()):
    filtered=sql._strip_uppercase_or(raw) if lab.endswith('medium') else raw
    query=sql.compose_query(filtered)
    expected,rows=baseline(query)
    budget=SQLBudget(LIMITS)
    resolve=run_bounded_query(query,LIMITS,authorize,budget=budget,initialize=seed)
    trace=run_bounded_query(query,LIMITS,authorize,budget=budget,initialize=seed)
    # Conservatively include an extra fixed comparison even when no tree exists.
    comparison=run_bounded_query("SELECT '1'='1'",LIMITS,authorize,budget=budget)
    analysis_budget=SQLBudget(LIMITS)
    expected_analysis,_=baseline(query,True)
    analysis=run_bounded_query(query,LIMITS,authorize,budget=analysis_budget,initialize=seed,compile_only=True)
    compatible=(resolve.status==trace.status==expected and resolve.rows==trace.rows==rows and comparison.status=='ok' and analysis.status==expected_analysis and analysis.rows==[])
    records.append(dict(lab=lab,input=raw,source=source_name,expected=expected,resolve=resolve.status,trace=trace.status,analysis=analysis.status,compatible=compatible,attempt_vm_charged=budget.steps,analysis_vm_charged=analysis_budget.steps,rows=len(resolve.rows)))
report=dict(python=platform.python_version(),sqlite=sqlite3.sqlite_version,source_sha=[v['sha'] for v in corpus['versions']],method='isolated helper simulation: resolve+trace+extra comparison share attempt budget; analysis is a separate request; no production route replacement',cases=records,summary=dict(cases=len(records),compatible=sum(r['compatible'] for r in records),max_attempt_vm=max(r['attempt_vm_charged'] for r in records),max_analysis_vm=max(r['analysis_vm_charged'] for r in records),max_rows=max(r['rows'] for r in records),policy_vm=LIMITS.vm_steps))
p=ROOT/'docs/verification/evidence/2026-10-28-issue42-sql-compatibility.json'
p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report['summary']))
assert all(r['compatible'] for r in records),'compatibility mismatch: see JSON'
