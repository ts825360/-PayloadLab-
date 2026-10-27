"""Audit CSV metadata and committed source proofs without executing payload strings."""
import csv,hashlib,json,subprocess
from collections import Counter,defaultdict
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'docs/datasets/payloads-all-the-things'
BASE='23b05593b73f6d9c9556eecd68abad5fbb8f6801'
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
 provenance=json.loads((DATA/'sources/SQL Injection__SQLite Injection.provenance.json').read_text(encoding='utf-8'))
 excerpt_path=provenance['local_path']
 retained=set(provenance['retained_ids'])
 assert provenance['source_commit']==manifest['source_commit']
 assert provenance['original_snapshot_git_commit']==BASE
 assert set(provenance['retained_original_proofs'])==retained
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
 assert retained=={r['id'] for r in rows if r['target_platform']=='sqlite'}
 for path in [*sorted(DATA.glob('*.csv')),DATA/'manifest.json']:
  original=subprocess.check_output(['git','show',BASE+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
  current=path.read_bytes()
  same=current==original
  if path.suffix=='.csv':assert same
  else:
   before=json.loads(original.decode('utf-8'))
   for key in retained:
    assert provenance['retained_original_proofs'][key]['original_proof']==before['entries'][key]
    assert provenance['retained_original_proofs'][key]['source_url']==next(r['source_url'] for r in rows if r['id']==key)
    for field in ['local_path','line_start','line_end','payload_sha256']:assert before['entries'][key][field]==manifest['entries'][key][field]
    before['entries'][key]=manifest['entries'][key]
   for entry in before['sources']:
    if entry['local_path']==excerpt_path:entry['sha256']=provenance['local_excerpt_sha256']
   assert before==manifest
  artifacts.append({'path':path.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(current).hexdigest(),'unchanged_from_base':same})
 source_bytes={};sources=[];unavailable=[]
 for entry in manifest['sources']:
  path=DATA/entry['local_path']
  raw=subprocess.check_output(['git','show',BASE+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
  is_excerpt=entry['local_path']==excerpt_path
  expected_upstream=provenance['upstream_full_sha256'] if is_excerpt else entry['sha256']
  assert hashlib.sha256(raw).hexdigest()==expected_upstream
  source_bytes[entry['local_path']]=raw
  record={'path':entry['local_path'],'upstream_committed_sha256_matches':True,'representation':'selected_excerpt' if is_excerpt else 'full_snapshot'}
  try:
   current=path.read_bytes()
   if is_excerpt:
    assert hashlib.sha256(current).hexdigest()==provenance['local_excerpt_sha256']==entry['sha256']
    for key in retained:
     prior=provenance['retained_original_proofs'][key]['original_proof']
     present=manifest['entries'][key]
     assert raw[prior['byte_start']:prior['byte_end']]==current[present['byte_start']:present['byte_end']]
     assert prior['line_start']==present['line_start'] and prior['line_end']==present['line_end']
    source_bytes[excerpt_path]=current
   else:assert current==raw
   record['working_copy_matches_manifest']=True
  except OSError as error:
   record.update(working_copy_matches_manifest=None,error=type(error).__name__)
   if is_excerpt:raise RuntimeError('Selected source excerpt unavailable') from error
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
 result={'base_commit':BASE,'source_commit_declared':manifest['source_commit'],'method':'Current source/manifest proof comparison; 9 full snapshots plus 1 explicit excerpt with original Git provenance; no payload execution','summaries':summaries,'total':len(rows),'labels':dict(Counter(r['label'] for r in rows)),'source_proofs':sources,'current_source_substring_proofs':len(manifest['entries']),'committed_substring_proofs':len(manifest['entries'])-len(retained),'excerpt_upstream_proofs':len(retained),'source_excerpt_provenance':provenance,'working_sources_unavailable':unavailable,'artifacts_unchanged':artifacts,'cross_label_equal_strings':collisions,'row_metadata_review':review,'working_copy_source_checks_complete':not unavailable,'working_copy_full_reproduction_complete':False,'offline_regeneration':{'status':'not_run_by_scope_audit','required_check':'separate test_dataset.py reproduction test'}}
 return result

if __name__=='__main__':
 result=audit()
 output=ROOT/'docs/verification/2026-10-27-csv-excerpt-audit.json';output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f"137 row metadata checks and {result['current_source_substring_proofs']} current byte/line proofs passed, including {result['excerpt_upstream_proofs']} excerpt-to-upstream proofs. Working source files available: {len(result['source_proofs'])-len(result['working_sources_unavailable'])}/{len(result['source_proofs'])}. Payload CSV files unchanged; manifest updates explicitly validated. No payload executed.")
 if result['working_sources_unavailable']:print('Working-copy full reproduction incomplete: '+', '.join(result['working_sources_unavailable']));raise SystemExit(2)
