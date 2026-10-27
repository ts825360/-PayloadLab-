"""Negative controls for the Git snapshot verifier; never alter repository source/data."""
import csv,unittest
from pathlib import Path
from unittest.mock import patch
from csv_snapshot_verification import SnapshotVerificationTests,ReadOnlyGitSource,DATA,NAMES
class SnapshotNegativeControls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  SnapshotVerificationTests.setUpClass()
  cls.fixture=SnapshotVerificationTests
 def test_rejects_ten_changed_source_hashes(self):
  for name,raw in self.fixture.sources.items():
   with self.subTest(source=name):
    changed=dict(self.fixture.sources);changed[name]=raw+b'\nchanged-source'
    with patch.object(self.fixture,'sources',changed):
     case=self.fixture('test_committed_source_bytes_and_105_original_builder_proofs')
     with self.assertRaises(AssertionError):case.test_committed_source_bytes_and_105_original_builder_proofs()
 def test_rejects_105_invented_payload_substrings(self):
  paths={entry['local_path']:entry['source_path'] for entry in self.fixture.manifest['sources']}
  count=0
  for name in NAMES[:-1]:
   with (DATA/name).open(encoding='utf-8-sig',newline='') as stream:
    for row in csv.DictReader(stream):
     if row['label']=='benign':continue
     proof=self.fixture.manifest['entries'][row['id']]
     with self.subTest(id=row['id']):
      with self.assertRaises(ValueError):self.fixture.builder.source_proof(paths[proof['local_path']],row['payload']+'\n__PAYLOADLAB_NEGATIVE_CONTROL_NOT_IN_SOURCE__')
     count+=1
  self.assertEqual(count,105)
 def test_rejects_ten_missing_in_memory_sources(self):
  for name in self.fixture.sources:
   with self.subTest(source=name):
    incomplete=dict(self.fixture.sources);del incomplete[name]
    with patch.object(self.fixture.builder,'ROOT',ReadOnlyGitSource(incomplete)):
     case=self.fixture('test_committed_source_bytes_and_105_original_builder_proofs')
     with self.assertRaises(KeyError):case.test_committed_source_bytes_and_105_original_builder_proofs()
 def test_rejects_each_changed_output_and_cleans_all_five_temporary_directories(self):
  original=self.fixture.builder.build
  for name in NAMES:
   with self.subTest(output=name):
    generated=[]
    def changed_output(output):
     counts=original(output);path=Path(output);generated.append(path)
     file=path/name;file.write_bytes(file.read_bytes()+b'\nchanged-output')
     return counts
    with patch.object(self.fixture.builder,'build',side_effect=changed_output):
     case=self.fixture('test_original_builder_reproduces_all_five_artifacts')
     with self.assertRaises(AssertionError):case.test_original_builder_reproduces_all_five_artifacts()
    self.assertEqual(len(generated),1)
    self.assertFalse(generated[0].exists())
 def test_rejects_three_source_path_escapes(self):
  source=ReadOnlyGitSource(self.fixture.sources)
  for relative in ['../outside.md','/outside.md','sources/../../outside.md']:
   with self.subTest(path=relative):
    with self.assertRaises(ValueError):source/relative
if __name__=='__main__':unittest.main()
