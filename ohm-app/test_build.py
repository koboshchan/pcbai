import unittest
from build import ohms,extract
from pathlib import Path
import tempfile
class ParseTest(unittest.TestCase):
 def test_values(self):
  for text,value in [('10k',10000),('4k7',4700),('24.9k',24900),('1M',1000000),('0R',0),('2R2',2.2)]:
   self.assertEqual(ohms(text),value)
  for text in ['DNP','DNP+','','POPULATION']:self.assertIsNone(ohms(text))
 def test_sources(self):
  import json
  bs=json.loads((Path(__file__).parent/'data/boards.json').read_text())
  self.assertEqual(len(bs),10)
  for b in bs:
   if b['name']!='DC1 universal':self.assertFalse(b['warnings'])
  dc3=next(b for b in bs if b['name']=='DC3')
  self.assertEqual(next(e for e in dc3['edges'] if e['ref']=='RF1')['r'],100000)
if __name__=='__main__':unittest.main()

