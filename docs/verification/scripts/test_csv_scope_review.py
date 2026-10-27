"""Text-only provenance controls; does not read or restore blocked source files."""
import copy,csv,json,unittest
from csv_scope_review import DATA,validate_row_metadata
class MetadataContractTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
  cls.rows=[]
  for path in sorted(DATA.glob('*.csv')):
   with path.open(encoding='utf-8-sig',newline='') as stream:cls.rows += [(path.stem,row) for row in csv.DictReader(stream)]
 def validate(self,kind,row):
  validate_row_metadata(row,kind,self.manifest['source_commit'],self.manifest['entries'].get(row['id']))
 def test_all_137_real_rows(self):
  self.assertEqual(len(self.rows),137)
  for kind,row in self.rows:
   with self.subTest(id=row['id']):self.validate(kind,row)
 def test_rejects_525_false_source_urls(self):
  count=0
  for kind,row in self.rows:
   if row['label']=='benign':continue
   url=row['source_url'];commit=self.manifest['source_commit']
   variants=[url.replace('github.com','example.invalid'),url.replace('/blob/','/other-path/'),url.replace(commit,'0'*40),url+'-wrong-line','']
   for changed in variants:
    altered=copy.deepcopy(row);altered['source_url']=changed
    with self.subTest(id=row['id'],case=count):
     with self.assertRaises(AssertionError):self.validate(kind,altered)
    count+=1
  self.assertEqual(count,525)
 def test_rejects_32_invented_benign_sources(self):
  count=0
  for kind,row in self.rows:
   if row['label']!='benign':continue
   altered=copy.deepcopy(row);altered['source_url']='https://example.invalid/claimed-source'
   with self.assertRaises(AssertionError):self.validate(kind,altered)
   count+=1
  self.assertEqual(count,32)
 def test_rejects_137_wrong_file_categories(self):
  for kind,row in self.rows:
   altered=copy.deepcopy(row);altered['attack_type']='different_category'
   with self.assertRaises(AssertionError):self.validate(kind,altered)
if __name__=='__main__':unittest.main()
