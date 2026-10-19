"""Deterministic endpointing checks; no fitting on validation/test."""
import unittest
import numpy as np
from temporal import voiced_bounds, pool_interval

class Temporal(unittest.TestCase):
    def test_silence_noise_and_continuous(self):
        for x in [np.zeros(16000), np.ones(16000)*.2,
                  np.random.default_rng(7).normal(0,.003,16000),
                  .2*np.sin(2*np.pi*800*np.arange(16000)/16000)]:
            self.assertEqual(voiced_bounds(x),(0,16000))

    def test_speech_noise_shift_margin(self):
        rng=np.random.default_rng(4)
        for start in [0, 2400, 8000]:
            x=rng.normal(0,.002,16000)
            x[start:start+4800] += .2*np.sin(2*np.pi*500*np.arange(4800)/16000)
            lo,hi=voiced_bounds(x)
            self.assertLessEqual(lo,start)
            self.assertGreaterEqual(hi,start+4800)
            self.assertLessEqual(start-lo,800)
            self.assertLessEqual(hi-(start+4800),800)
            self.assertLess(hi-lo,7000)

    def test_click_and_disjoint_regions(self):
        x=np.zeros(16000);x[1200]=1
        self.assertEqual(voiced_bounds(x),(0,16000))
        x[4000:5600]=.3*np.sin(np.arange(1600))
        x[8000:9600]=.3*np.sin(np.arange(1600))
        lo,hi=voiced_bounds(x)
        self.assertGreater(lo,1200)
        self.assertLessEqual(lo,4000)
        self.assertGreaterEqual(hi,9600)

    def test_fractional_pooling(self):
        np.testing.assert_allclose(pool_interval(np.ones((4,16000)),123.5,12345.5,16),1)
        x=np.arange(16).reshape(2,8)
        np.testing.assert_allclose(pool_interval(x,0,8,4),x.reshape(2,4,2).mean(-1))
        np.testing.assert_allclose(pool_interval(np.arange(4),.5,3.5,3),[.5,1.5,2.5])
        with self.assertRaises(ValueError):pool_interval(x,2,1,4)
        with self.assertRaises(ValueError):voiced_bounds(np.zeros(100))

if __name__=="__main__":unittest.main()
