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
 def test_short_word_silence_before_frontend(self):
    from unittest.mock import patch
    rng=np.random.default_rng(93)
    for region in [(0,2000),(14000,16000),(5000,7000)]:
     a=rng.normal(0,.8,16000).astype("float32")
     b=rng.normal(0,.8,16000).astype("float32")
     b[region[0]:region[1]]=a[region[0]:region[1]]
     expected=np.zeros(16000,dtype="float32")
     expected[region[0]:region[1]]=a[region[0]:region[1]]
     np.testing.assert_array_equal(augmentation_audio(a,region),expected)
     for start in starts_for_region(region):
      w=padded_window(augmentation_audio(a,region),start)
      lo,hi=region[0]-start,region[1]-start
      np.testing.assert_array_equal(w[lo:hi],a[region[0]:region[1]])
      self.assertTrue(np.all(w[:lo]==0));self.assertTrue(np.all(w[hi:]==0))
     for label in LABELS:
      with patch("window400.detected_region",return_value=region):
       fa=augmented_features(a,label);fb=augmented_features(b,label)
      np.testing.assert_array_equal(fa,fb)
      np.testing.assert_array_equal(fa,raw_features(expected,starts_for_region(region),label))
      self.assertFalse(np.array_equal(raw_features(a,[region[0]],label),raw_features(b,[region[0]],label)))
 def test_long_and_fallback_keep_context(self):
    from unittest.mock import patch
    a=np.random.default_rng(9).normal(0,.1,16000).astype("float32")
    for region in [None,(1000,9000),(1000,7400)]:
     np.testing.assert_array_equal(augmentation_audio(a,region),a)
     for label in LABELS:
      with patch("window400.detected_region",return_value=region):
       f=augmented_features(a,label)
      np.testing.assert_array_equal(f,raw_features(a,starts_for_region(region),label))
 def test_grouped_score_not_vote(self):
    from train400 import evaluate_scores
    s=torch.zeros((1,3,10),device="cuda",dtype=torch.float64)
    s[0,0,0]=2;s[0,1,0]=2;s[0,2,1]=10
    got=evaluate_scores(s,torch.tensor([0,0,0],device="cuda"),1)
    self.assertEqual(got.argmax(2).item(),1)
if __name__=="__main__":unittest.main()
