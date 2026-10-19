"""Validate delivered experimental results without downloading or heavy computation."""
import json,unittest
from pathlib import Path
H=Path(__file__).resolve().parent
class Results(unittest.TestCase):
 def test_results(self):
  for name in ['8x8','16x4','4x16','4x16-alt']:
   m=json.loads((H/name/'metrics.json').read_text());p=json.loads((H/f'preprocess_{name}.json').read_text())
   self.assertEqual(m['counts'],{'train':31158,'validation':3643,'test':4107})
   self.assertTrue(p['speaker_sets_disjoint']);self.assertEqual(len(p['lo']),64);self.assertEqual(len(p['hi']),64)
   self.assertFalse(m['test_used_for_selection'])
   if name.startswith('4x16'):
    front=p['frontend']
    self.assertEqual(p['bands'],4);self.assertEqual(p['slices'],16)
    self.assertEqual(front['samples_per_frame']*p['slices'],16000)
    self.assertEqual(front['centers_hz'],[1600,2000,2500,3150] if name=='4x16' else [500,1000,2000,4000])
    self.assertEqual(len(front['sos']),4)
    self.assertEqual(front['flattening'],'band-major')
   for key,acc in [('float_confusion','float_test_accuracy'),('hardware_confusion','hardware_nominal_accuracy')]:
    cm=m[key];self.assertEqual(sum(map(sum,cm)),4107)
    self.assertAlmostEqual(sum(cm[i][i] for i in range(10))/4107,m[acc])
   samples=m['mc']['accuracy_samples'];self.assertEqual(len(samples),1000)
   self.assertAlmostEqual(sum(samples)/1000,m['mc']['mean']);self.assertEqual(min(samples),m['mc']['min'])
   for r in m['solver_regression']:self.assertLess(max(r['errors']),1e-9)
   c=json.loads((H/name/'circuit.json').read_text())
   self.assertEqual(len(c['layer1']),16);self.assertEqual(len(c['layer2']),10)
 def test_selection(self):
  s=json.loads((H/'summary.json').read_text())
  self.assertEqual(len(s['results']),4)
  self.assertEqual(s['chosen_by_hardware_validation'],max(s['results'],key=lambda m:m['hardware_validation'])['layout'])
if __name__=='__main__':unittest.main()
