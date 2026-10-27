"""Audit CSV metadata and committed source proofs without executing payload strings."""
import csv,hashlib,json,subprocess
from collections import Counter,defaultdict
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'docs/datasets/payloads-all-the-things'
BASE='fd106c93c4c37375bcc43aca4249dceea0dbeb12'
FIELDS='id,payload,label,attack_type,technique,target_platform,input_context,variant_type,family_id,source_url,source_commit,label_reason,validation_status,license'.split(',')
def validate_row_metadata(row,expected_kind,source_commit,proof=None):
 assert row['attack_type']==expected_kind
 assert row['label'] in {'attack','benign','uncertain'}
 assert row['id'].startswith(f"{expected_kind}-{row['label']}-")
 assert row['validation_status']=='documentation_reviewed_not_executed'
 assert row['license']=='MIT'
 assert all(row[k] for k in FIELDS if k not in ('source_url','source_commit'))
 if row['label']=='benign':
  assert row['source_url']==row['source_commit']==''
 else:
  assert proof is not None
  source_path=proof['local_path'].removeprefix('sources/').replace('__','/')
  expected=f"https://github.com/swisskyrepo/PayloadsAllTheThings/blob/{source_commit}/{quote(source_path)}#L{proof['line_start']}-L{proof['line_end']}"
  assert row['source_url']==expected
  assert row['source_commit']==source_commit
 if row['label']=='uncertain':assert 'review_only' in row['label_reason']

def audit():
 manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
 rows=[];summaries={};artifacts=[]
 for path in sorted(DATA.glob('*.csv')):
  with path.open(encoding='utf-8-sig',newline='') as f:
   reader=csv.DictReader(f);assert reader.fieldnames==FIELDS
   group=list(reader)
  assert path.read_bytes().startswith(b'\xef\xbb\xbf')
  for row in group:validate_row_metadata(row,path.stem,manifest['source_commit'],manifest['entries'].get(row['id']))
  rows+=group
  summaries[path.stem]={'count':len(group),'labels':dict(Counter(r['label'] for r in group)),'platforms':dict(Counter(r['target_platform'] for r in group)),'techniques':dict(Counter(r['technique'] for r in group))}
  assert summaries[path.stem]['labels']==manifest['counts'][path.stem]
 for path in [*sorted(DATA.glob('*.csv')),DATA/'manifest.json']:
  original=subprocess.check_output(['git','show',BASE+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
  current=path.read_bytes();assert current==original
  artifacts.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(current).hexdigest(),'unchanged_from_base':True})
 source_bytes={};sources=[];unavailable=[]
 for entry in manifest['sources']:
  path=DATA/entry['local_path']
  raw=subprocess.check_output(['git','show',BASE+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
  assert hashlib.sha256(raw).hexdigest()==entry['sha256']
  source_bytes[entry['local_path']]=raw
  record={'path':entry['local_path'],'committed_sha256_matches':True}
  try:
   current=path.read_bytes();assert current==raw
   record['working_copy_matches']=True
  except OSError as error:
   record.update(working_copy_matches=None,error=type(error).__name__)
   unavailable.append(entry['local_path'])
  sources.append(record)
 assert len(rows)==137 and len({r['id'] for r in rows})==137
 assert set(manifest['entries'])=={r['id'] for r in rows if r['label']!='benign'}
 review=[];by_payload=defaultdict(list)
 for row in rows:
  assert row['validation_status']=='documentation_reviewed_not_executed'
  assert row['license']=='MIT'
  assert all(row[k] for k in FIELDS if k not in ('source_url','source_commit'))
  if row['label']=='benign':assert row['source_url']==row['source_commit']==''
  else:
   proof=manifest['entries'][row['id']];raw=source_bytes[proof['local_path']];snippet=raw[proof['byte_start']:proof['byte_end']]
   assert snippet==row['payload'].encode('utf-8')
   assert hashlib.sha256(snippet).hexdigest()==proof['payload_sha256']
   assert raw[:proof['byte_start']].count(b'\n')+1==proof['line_start']
   assert raw[:proof['byte_end']-1].count(b'\n')+1==proof['line_end']
   assert row['source_commit']==manifest['source_commit']
   assert '/blob/'+manifest['source_commit']+'/' in row['source_url']
   assert row['source_url'].endswith(f"#L{proof['line_start']}-L{proof['line_end']}")
  if row['label']=='uncertain':assert 'review_only' in row['label_reason']
  review.append({k:row[k] for k in FIELDS if k!='payload'})
  by_payload[row['payload']].append(row)
 collisions=[{'ids':[r['id'] for r in group],'labels':[r['label'] for r in group],'contexts':[r['input_context'] for r in group]} for group in by_payload.values() if len({r['label'] for r in group})>1]
 result={'base_commit':BASE,'source_commit_declared':manifest['source_commit'],'method':'CSV text parsing and committed Git blob/manifest proof comparison; no payload execution or remote authenticity verification','summaries':summaries,'total':len(rows),'labels':dict(Counter(r['label'] for r in rows)),'source_proofs':sources,'committed_substring_proofs':len(manifest['entries']),'working_sources_unavailable':unavailable,'artifacts_unchanged':artifacts,'cross_label_equal_strings':collisions,'row_metadata_review':review,'working_copy_source_checks_complete':not unavailable,'working_copy_full_reproduction_complete':False,'offline_regeneration':{'status':'not_run_by_scope_audit','required_check':'separate test_dataset.py reproduction test'}}
 return result

if __name__=='__main__':
 result=audit()
 output=ROOT/'docs/verification/2026-10-27-csv-scope-audit.json';output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f"137 row metadata checks, {len(result['source_proofs'])} committed source hashes and {result['committed_substring_proofs']} committed byte/line proofs passed. Working source files available: {len(result['source_proofs'])-len(result['working_sources_unavailable'])}/{len(result['source_proofs'])}. CSV/manifest unchanged: {len(result['artifacts_unchanged'])}. Cross-label equal-string groups: {len(result['cross_label_equal_strings'])}. No payload executed.")
 if result['working_sources_unavailable']:print('Working-copy full reproduction incomplete: '+', '.join(result['working_sources_unavailable']));raise SystemExit(2)
