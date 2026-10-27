"""Export bounded permissions before/after evidence; never execute host commands."""
import json
from pathlib import Path
import subprocess
import sys
import types
ROOT=Path(__file__).resolve().parents[3]
BASE='9b43f5727f4eac693bb37254173d05d2be4c23f9'
sys.path.insert(0,str(ROOT/'backend'))
from app.routes.labs import analyze_lab,attempt_lab
source=subprocess.check_output(['git','show',f'{BASE}:backend/app/labs/practice_extensions.py'],cwd=ROOT).decode('utf-8')
old=types.ModuleType('permission_review_base');exec(compile(source,f'{BASE}:practice_extensions.py','exec'),old.__dict__)
CASES=[
 ('PERM-01','whoami',[], 'command_ok','student'),
 ('PERM-02','ls -l /lab/report.txt',[], 'command_ok','student'),
 ('PERM-03','cat /lab/report.txt',[], 'permission_denied','student'),
 ('PERM-04','cat /lab/readme.txt',[], 'command_ok','student'),
 ('PERM-05','sudo -l',[], 'command_ok','student'),
 ('PERM-06','sudo /lab/maintenance',['sudo -l'], 'elevated','root'),
 ('PERM-07','cat /lab/report.txt',['sudo -l','sudo /lab/maintenance'], 'command_ok','root'),
 ('PERM-08','exit',['sudo /lab/maintenance'], 'command_ok','student'),
 ('PERM-09','chmod 777 /lab/report.txt',[], 'unsupported','student'),
]
records=[]
for case_id,command,history,expected,user in CASES:
 payload=dict(command=command,history=history)
 result=attempt_lab('permissions-easy',payload);after=result.learning_trace
 before=old.get_extension_trace('permissions-easy',payload)
 analysis=analyze_lab('permissions-easy',payload)
 assert after['execution']['status']==before['execution']['status']==expected
 assert after['terminal']['current_user']==user
 assert analysis['execution'] is None
 assert analysis['terminal']['current_user']==('root' if 'sudo /lab/maintenance' in history else 'student')
 assert result.success is (command=='cat /lab/report.txt' and user=='root')
 records.append(dict(id=case_id,payload=payload,expected_status=expected,actual_status=after['execution']['status'],current_user=user,goal=result.success,before=before,after=after,analysis=analysis))
output=ROOT/'docs/verification/2026-10-27-permissions-review-cases.json'
output.write_text(json.dumps(dict(base_commit=BASE,method='direct route function calls; no host shell/files',case_count=len(records),cases=records),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'{len(records)} permission cases matched status, identity, goal and pending analysis')
