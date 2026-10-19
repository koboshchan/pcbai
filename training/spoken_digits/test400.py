"""Contract tests; run on cached KAT-BOX dependencies."""
import unittest
import numpy as np
import torch
from window400 import *
class Windows(unittest.TestCase):
 def test_sliding(self):
    self.assertEqual(starts_for_region((1000,9000)),[1000,2600])
    self.assertEqual(starts_for_region((1000,9500)),[1000,2600,3100])
    self.assertEqual(starts_for_region((1000,7400)),[1000])
    self.assertEqual(starts_for_region(None),list(range(0,9601,1600)))
 def test_short(self):
    self.assertEqual(starts_for_region((100,4100)),[-2300,100,-1100])
    a=np.arange(16000)+1
    for region in [(0,2000),(14000,16000),(5000,7000)]:
     for s in starts_for_region(region):
      w=padded_window(a,s);self.assertEqual(w.shape,(6400,))
      self.assertTrue(s<=region[0] and s+6400>=region[1])
      lo=max(0,s);hi=min(16000,s+6400)
      np.testing.assert_array_equal(w[lo-s:hi-s],a[lo:hi])
      self.assertTrue(np.all(w[:lo-s]==0));self.assertTrue(np.all(w[hi-s:]==0))
 def test_fallback(self):
    ss,on=windows(np.zeros(16000));self.assertEqual(ss,starts_for_region(None));self.assertEqual(on,0)
 def test_durations(self):
    for length in [1,2000,6399,6400,6401,8000,8500,16000]:
     for s in starts_for_region((0,length)):
      self.assertEqual(len(padded_window(np.ones(16000),s)),6400)
 def test_frontend(self):
    a=np.random.default_rng(1).normal(0,.01,16000).astype("float32")
    for label in LABELS:
     f=raw_features(a,[-4000,0,9600,14000],label)
     self.assertEqual(f.shape,(4,64));self.assertTrue(np.isfinite(f).all())
     np.testing.assert_array_equal(f[1],raw_features(a,[0],label)[0])
 def test_grouped_score_not_vote(self):
    from train400 import evaluate_scores
    s=torch.zeros((1,3,10),device="cuda",dtype=torch.float64)
    s[0,0,0]=2;s[0,1,0]=2;s[0,2,1]=10
    got=evaluate_scores(s,torch.tensor([0,0,0],device="cuda"),1)
    self.assertEqual(got.argmax(2).item(),1)
if __name__=="__main__":unittest.main()
