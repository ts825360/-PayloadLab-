"""Offline integrity checks. Payload strings are never executed or fetched."""
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent
FIELDS = 'id,payload,label,attack_type,technique,target_platform,input_context,variant_type,family_id,source_url,source_commit,label_reason,validation_status,license'.split(',')
TYPES = ('sql_injection', 'xss', 'command_injection', 'ssrf')
COMMIT = '3ac27901c711bdf3f5b65a7b1d1820a1f65bd09a'


class BuildContractTests(unittest.TestCase):
    def test_offline_builder_exists(self):
        self.assertTrue((ROOT / 'build_dataset.py').is_file(), 'Offline dataset builder has not been implemented')


@unittest.skipUnless(all((ROOT / (kind + '.csv')).is_file() for kind in TYPES), 'Dataset has not been generated yet')
class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = []
        cls.by_type = {}
        for kind in TYPES:
            with (ROOT / (kind + '.csv')).open(encoding='utf-8-sig', newline='') as handle:
                reader = csv.DictReader(handle)
                cls.by_type[kind] = list(reader)
                cls.rows.extend(cls.by_type[kind])
        cls.proofs = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))

    def test_exact_schema_and_bom(self):
        for kind in TYPES:
            path = ROOT / (kind + '.csv')
            self.assertTrue(path.read_bytes().startswith(b'\xef\xbb\xbf'))
            with path.open(encoding='utf-8-sig', newline='') as handle:
                self.assertEqual(next(csv.reader(handle)), FIELDS)

    def test_unique_ids_counts_and_required_metadata(self):
        self.assertEqual(len({row['id'] for row in self.rows}), len(self.rows))
        self.assertGreaterEqual(len(self.rows), 120)
        self.assertLessEqual(len(self.rows), 180)
        for kind, rows in self.by_type.items():
            counts = Counter(row['label'] for row in rows)
            self.assertTrue(20 <= counts['attack'] <= 40, (kind, counts))
            self.assertTrue(8 <= counts['benign'] <= 12, (kind, counts))
            for row in rows:
                self.assertEqual(row['attack_type'], kind)
                self.assertEqual(set(row), set(FIELDS))
                self.assertTrue(all(row[field] for field in FIELDS if field not in ('source_url', 'source_commit')))
                self.assertEqual(row['validation_status'], 'documentation_reviewed_not_executed')
                self.assertEqual(row['license'], 'MIT')

    def test_source_bytes_substrings_hashes_and_line_citations(self):
        proofs = self.proofs['entries']
        for source in self.proofs['sources']:
            raw = (ROOT / source['local_path']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])
        for row in self.rows:
            if row['label'] == 'benign':
                self.assertEqual(row['source_url'], '')
                self.assertEqual(row['source_commit'], '')
                continue
            proof = proofs[row['id']]
            raw = (ROOT / proof['local_path']).read_bytes()
            snippet = raw[proof['byte_start']:proof['byte_end']]
            self.assertEqual(snippet, row['payload'].encode('utf-8'), row['id'])
            self.assertEqual(hashlib.sha256(snippet).hexdigest(), proof['payload_sha256'])
            self.assertEqual(raw[:proof['byte_start']].count(b'\n') + 1, proof['line_start'])
            self.assertEqual(raw[:proof['byte_end'] - 1].count(b'\n') + 1, proof['line_end'])
            self.assertEqual(row['source_commit'], COMMIT)
            self.assertTrue(row['source_url'].endswith(f"#L{proof['line_start']}-L{proof['line_end']}"))
            self.assertIn('/blob/' + COMMIT + '/', row['source_url'])

    def test_platform_coverage_variant_families_and_multiline(self):
        sql = self.by_type['sql_injection']
        self.assertTrue({'mysql', 'mssql', 'postgresql', 'sqlite', 'oracle', 'common'} <= {r['target_platform'] for r in sql})
        for kind, rows in self.by_type.items():
            families = defaultdict(list)
            for row in rows:
                families[row['family_id']].append(row)
            self.assertTrue(any(len(group) >= 2 and len({r['payload'] for r in group}) >= 2 for group in families.values()), kind)
            self.assertTrue(any('encoded' in r['variant_type'] or 'obfuscated' in r['variant_type'] for r in rows), kind)
        self.assertTrue(any('\n' in row['payload'] for row in self.rows))
        self.assertTrue(any('＂' in row['payload'] for row in self.rows))
        self.assertTrue(any('\x0c' in row['payload'] for row in self.rows))

    def test_uncertain_review_only_and_documented_limits(self):
        self.assertTrue(any(row['label'] == 'uncertain' for row in self.rows))
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        for phrase in ('uncertain', 'review_only', 'family_id', 'Excel', '미실행', '학습', '성공'):
            self.assertIn(phrase, readme)
        for row in self.rows:
            self.assertNotIn('exploit_successful', row['validation_status'])
            if row['label'] == 'uncertain':
                self.assertIn('review_only', row['label_reason'])

    def test_generator_reproduces_committed_artifacts_offline(self):
        with tempfile.TemporaryDirectory() as output:
            subprocess.run([sys.executable, str(ROOT / 'build_dataset.py'), '--output-dir', output], check=True, capture_output=True)
            for name in (*[kind + '.csv' for kind in TYPES], 'manifest.json'):
                self.assertEqual((ROOT / name).read_bytes(), (Path(output) / name).read_bytes(), name)


if __name__ == '__main__':
    unittest.main()
