"""Synthetic front-end checks; run on KAT-BOX alongside training."""
import unittest
import numpy as np
from scipy.signal import sosfreqz
from prepare import BAND_SETS, envelope_filters, envelope_features


class Envelopes(unittest.TestCase):
    def test_filter_edges(self):
        for centers in BAND_SETS.values():
            for center, sos in zip(centers, envelope_filters(centers)):
                edges = [center / 2**(1/6), center * 2**(1/6)]
                _, response = sosfreqz(sos, worN=edges, fs=16000)
                np.testing.assert_allclose(abs(response), 1/np.sqrt(2), atol=1e-10)
                self.assertEqual(sos.shape, (2, 6))

    def test_silence_and_shape(self):
        x = envelope_features(np.zeros((2, 16000)), envelope_filters(BAND_SETS["4x16"]))
        self.assertEqual(x.shape, (2, 64))
        np.testing.assert_array_equal(x, -10)
        with self.assertRaises(ValueError):
            envelope_features(np.zeros((2, 15999)), envelope_filters([1600]))

    def test_band_order_and_no_future_leak(self):
        t = np.arange(16000)/16000
        centers = BAND_SETS["4x16"]
        audio = np.array([np.sin(2*np.pi*c*t) for c in centers])
        features = envelope_features(audio, envelope_filters(centers)).reshape(4,4,16)
        np.testing.assert_array_equal(features[:,:,4:].mean(-1).argmax(1), np.arange(4))
        # A late impulse cannot affect previous windows (no zero-phase filtering).
        audio = np.zeros((1,16000))
        audio[0,8000] = 1
        features = envelope_features(audio, envelope_filters(centers)).reshape(4,16)
        np.testing.assert_array_equal(features[:,:8], -10)
        self.assertTrue(np.any(features[:,8] > -10))

if __name__ == "__main__":
    unittest.main()
