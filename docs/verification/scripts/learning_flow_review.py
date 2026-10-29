"""Compare all available guided examples with actual route output; no external requests."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'backend'))
from app.routes.labs import get_labs,attempt_lab,analyze_lab
script=ROOT/'docs/verification/scripts/learning_flow_review.mjs'
catalog=json.loads(subprocess.check_output(['node',str(script),'catalog'],cwd=ROOT).decode('utf-8'))
assert {lab.id for lab in get_labs()}=={lab['id'] for lab in catalog}
for lab in catalog:
 history=[];observations=[]
 for step in lab['lesson']['steps']:
  value=int(step['suggestion']) if lab['numeric'] else step['suggestion']
  payload={lab['field']:value}
  if lab['category']=='idor' and lab['difficulty']=='medium':payload['claimed_user_id']=2001
  if lab['category']=='permissions':payload['history']=list(history)
  result=attempt_lab(lab['id'],payload).model_dump()
  analysis=analyze_lab(lab['id'],payload)
  assert analysis['execution'] is None
  observations.append(dict(step_id=step['id'],payload=payload,result=result,analysis=analysis))
  if lab['category']=='permissions':history.append(value)
 lab['observations']=observations
 lab['probes']=[]
 def probe(step_id,value,expected,**extra):
  payload={lab['field']:int(value) if lab['numeric'] else value,**extra}
  lab['probes'].append(dict(step_id=step_id,payload=payload,expected_accept=expected,
                           result=attempt_lab(lab['id'],payload).model_dump(),analysis=analyze_lab(lab['id'],payload)))
 category=lab['category'];last=lab['lesson']['steps'][-1]['id']
 if category=='sql_injection':probe(last,'admin',False)
 elif category=='reflected_xss':probe(last,'hello',False)
 elif category=='idor':probe(last,1043 if lab['difficulty']=='medium' else 1042,False,**({'claimed_user_id':1} if lab['difficulty']=='medium' else {}))
 elif category=='ssrf':probe(last,'https://example.com/',False)
 elif category=='command_injection':probe(last,'example.com',False)
 elif category=='linux_basics':probe(last,'pwd',False)
 else:
  for command in ['ls -l /lab','ls -l /lab/report.txt','  ls -l /lab  ']:probe('perm-file',command,True,history=[])
  for command in ['pwd','ls /lab','ls -l /etc']:probe('perm-file',command,False,history=[])
output=ROOT/'docs/verification/2026-10-27-learning-flow-cases.json'
output.write_text(json.dumps(dict(method='direct local route calls plus frontend lesson.accept checks; not browser execution proof',baseline='8ee07de2774b3d67fa7c8e270673f56551a454c1',labs=catalog),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
subprocess.run(['node',str(script),'verify'],cwd=ROOT,check=True)
