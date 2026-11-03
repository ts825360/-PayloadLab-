"""Read existing authorizers and replay small local ASGI cases; no policy activation."""
import ast, hashlib, json, platform, sqlite3, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'backend'))
from tests.test_review_app import client
from tests.test_request_limits import TestClient
from app.main import app
files=['docs/verification/scripts/issue42_review_server.py','backend/tests/test_sql_limits.py','docs/verification/scripts/issue44_policy_measure.py']
inventories=[]
for name in files:
    raw=(ROOT/name).read_bytes()
    tree=ast.parse(raw)
    sets=[sorted(n.elts[i].value for i in range(len(n.elts))) for n in ast.walk(tree) if isinstance(n,ast.Set) and all(isinstance(v,ast.Constant) and isinstance(v.value,str) for v in n.elts)]
    assert ['length','printf','sum'] in sets
    inventories.append(dict(path=name,sha256=hashlib.sha256(raw).hexdigest(),functions=['length','printf','sum']))
cases=[
('name','박태성','easy','empty','empty'),
('admin','admin','easy','empty','empty'),
('empty','','easy','empty','empty'),
('quote',"admin'",'easy','syntax_error','syntax_error'),
('missing_or',"admin' '1'='1'--",'easy','syntax_error','syntax_error'),
('success',"admin' OR '1'='1'--",'easy','rows','rows'),
('normal_filter',"admin' OR '1'='1'--",'medium','syntax_error','syntax_error'),
('normal_bypass',"admin' oR '1'='1'--",'medium','rows','rows'),
('length',"' UNION SELECT 3,length('abc'),''--",'easy','rows','rows'),
('printf',"' UNION SELECT 3,printf('%s','abc'),''--",'easy','rows','rows'),
('sum',"' UNION SELECT 3,sum(id),'' FROM users--",'easy','rows','rows'),
('unsupported_function',"' UNION SELECT 3,sqlite_version(),''--",'easy','rows','blocked'),
('union_constants',"' UNION SELECT 3,'learner','dummy'--",'easy','rows','rows'),
]
records=[]
for mode,c in [('default',TestClient(app)),('review',client())]:
    for label,value,difficulty,expected_default,expected_review in cases:
        r=c.post('/labs/sql-injection-'+difficulty+'/attempt',json={'username':value})
        body=r.json(); trace=body['learning_trace']; actual=trace['execution']['status']
        expected=expected_default if mode=='default' else expected_review
        if expected=='rows': assert body['success'] and trace['execution']['count']>0,(mode,label,trace)
        else: assert actual==expected,(mode,label,actual,expected)
        records.append(dict(mode=mode,case=label,input=value,difficulty=difficulty,http_status=r.status_code,expected=expected,actual=actual,success=body['success'],lens_id=trace['lens']['id'],lens_what=trace['lens'].get('what'),passed=True))
result=dict(source_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),environment=dict(python=platform.python_version(),sqlite=sqlite3.sqlite_version,os=platform.platform()),scope='26 local in-process ASGI requests; existing test policy only; not browser/TCP/load/production activation',authorizers=inventories,cases=records,passed=len(records))
target=ROOT/'docs/verification/evidence/2026-11-03-sql-function-inventory.json'
target.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(passed=len(records),evidence=str(target)),ensure_ascii=True))
