"""Verify committed documentation bytes and original builder output without restoring source files.

Source Markdown stays in memory; only CSV/manifest outputs enter a checked temporary directory.
This does not make the ordinary working-copy test_dataset.py pass when its source is absent.
"""
import csv,hashlib,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path,PurePosixPath
ROOT=Path(__file__).resolve().parents[3]
DATA=ROOT/'docs/datasets/payloads-all-the-things'
BASE='23b05593b73f6d9c9556eecd68abad5fbb8f6801'
NAMES=['sql_injection.csv','xss.csv','command_injection.csv','ssrf.csv','manifest.json']
SUMMARY={}
def git_bytes(path):
 return subprocess.check_output(['git','show',BASE+':'+path.relative_to(ROOT).as_posix()],cwd=ROOT)
class ReadOnlyGitSource:
 def __init__(self,files,relative=''):self.files,self.relative=files,relative
 def __truediv__(self,part):
  relative=(PurePosixPath(self.relative)/part).as_posix()
  if relative.startswith('/') or '..' in PurePosixPath(relative).parts:raise ValueError('Source outside snapshot')
  return ReadOnlyGitSource(self.files,relative)
 @property
 def name(self):return PurePosixPath(self.relative).name
 def read_bytes(self):return self.files[self.relative]
 def glob(self,pattern):
  if self.relative!='sources' or pattern!='*.md':raise ValueError('Only snapshot source enumeration is supported')
  return [ReadOnlyGitSource(self.files,name) for name in self.files]
 def __lt__(self,other):return Path(self.relative)<Path(other.relative)
class SnapshotVerificationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  # This verifier intentionally preserves the archived full-source baseline.
  for name in [*NAMES[:-1],'build_dataset.py','curated_samples.py']:
   path=DATA/name
   current=path.read_bytes();committed=git_bytes(path)
   if name.endswith('.py'):
    current=current.replace(b'\r\n',b'\n');committed=committed.replace(b'\r\n',b'\n')
   if current!=committed:raise AssertionError('Working artifact/code differs from selected base: '+name)
  cls.manifest=json.loads(git_bytes(DATA/'manifest.json').decode('utf-8'))
  cls.sources={entry['local_path']:git_bytes(DATA/entry['local_path']) for entry in cls.manifest['sources']}
  sys.path.insert(0,str(DATA))
  spec=importlib.util.spec_from_file_location('payloadlab_snapshot_builder',DATA/'build_dataset.py')
  cls.builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(cls.builder)
  cls.builder.ROOT=ReadOnlyGitSource(cls.sources)
  SUMMARY.update(base_commit=BASE,method='original unchanged builder with a read-only in-memory Git source provider and real temporary CSV/manifest outputs',source_markdown_written=False,security_settings_changed=False,generator_and_curated_code_match_base=True,code_comparison="Python CRLF/LF normalized; CSV/manifest/source bytes exact",working_source_present=(DATA/'sources/SQL Injection__SQLite Injection.md').exists(),source_count=len(cls.sources),expected_artifacts_mode='selected Git baseline blobs; current excerpt manifest is verified by test_dataset.py',ordinary_working_copy_test_status='working source representation is checked separately by ordinary test_dataset.py')
 def test_committed_source_bytes_and_105_original_builder_proofs(self):
  hashes=[];proofs=0
  paths={entry['local_path']:entry['source_path'] for entry in self.manifest['sources']}
  for entry in self.manifest['sources']:
   actual=hashlib.sha256(self.sources[entry['local_path']]).hexdigest()
   self.assertEqual(actual,entry['sha256']);hashes.append(dict(path=entry['local_path'],sha256=actual))
  for name in NAMES[:-1]:
   with (DATA/name).open(encoding='utf-8-sig',newline='') as stream:
    for row in csv.DictReader(stream):
     if row['label']=='benign':continue
     expected=self.manifest['entries'][row['id']]
     url,proof=self.builder.source_proof(paths[expected['local_path']],row['payload'])
     self.assertEqual(proof,expected,row['id']);self.assertEqual(url,row['source_url'],row['id']);proofs+=1
  self.assertEqual(proofs,105);SUMMARY.update(source_hashes=hashes,source_proofs_verified=proofs)
 def test_original_builder_reproduces_all_five_artifacts(self):
  artifacts=[]
  with tempfile.TemporaryDirectory(prefix='payloadlab-csv-proof-') as output:
   temp=Path(output).resolve()
   self.assertEqual(temp.parent,Path(tempfile.gettempdir()).resolve())
   self.assertTrue(temp.name.startswith('payloadlab-csv-proof-'))
   counts=self.builder.build(temp)
   self.assertEqual(counts,self.manifest['counts'])
   self.assertEqual({p.name for p in temp.iterdir()},set(NAMES))
   for name in NAMES:
    generated=(temp/name).read_bytes();expected=git_bytes(DATA/name)
    self.assertEqual(generated,expected,name)
    artifacts.append(dict(name=name,bytes=len(generated),sha256=hashlib.sha256(generated).hexdigest(),byte_identical=True))
  SUMMARY.update(reproduced_artifacts=artifacts,temporary_outputs_cleaned=not temp.exists())
if __name__=='__main__':
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(SnapshotVerificationTests)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 SUMMARY.update(snapshot_tests_run=result.testsRun,snapshot_tests_passed=result.wasSuccessful())
 out=ROOT/'docs/verification/2026-10-27-csv-snapshot-verification.json'
 out.write_text(json.dumps(SUMMARY,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 raise SystemExit(0 if result.wasSuccessful() else 1)
