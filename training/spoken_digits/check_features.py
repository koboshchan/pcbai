"""Check cached splits and reproduce sampled four-band features on KAT-BOX."""
import json
from pathlib import Path
import wave
import numpy as np
from prepare import BAND_SETS, envelope_filters, envelope_features

H = Path(__file__).resolve().parent

def main():
    baseline = np.load(H / "data/features_8x8.npz")
    for label, centers in BAND_SETS.items():
        data = np.load(H / f"data/features_{label}.npz")
        meta = json.loads((H / f"preprocess_{label}.json").read_text())
        for key in ("names", "y", "split"):
            np.testing.assert_array_equal(data[key], baseline[key])
        assert data["X"].shape == (38908, 64)
        assert np.isfinite(data["X"]).all()
        assert data["X"].min() >= 0 and data["X"].max() <= 5
        np.testing.assert_allclose(data["X"] / 5 * 63,
                                   np.round(data["X"] / 5 * 63), atol=1e-5)
        np.testing.assert_array_equal(data["lo"], meta["lo"])
        np.testing.assert_array_equal(data["hi"], meta["hi"])
        assert np.all(data["hi"] > data["lo"])
        # Two clips per digit per split, selected by fixed index, not accuracy.
        ids = [i for digit in range(10) for split in range(3)
               for i in np.flatnonzero((data["y"] == digit) & (data["split"] == split))[:2]]
        audio = []
        for i in ids:
            with wave.open(str(H / "data" / str(data["names"][i]))) as wav:
                assert (wav.getframerate(), wav.getnchannels(), wav.getsampwidth()) == (16000, 1, 2)
                samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2").astype(np.float32) / 32768
            audio.append(np.pad(samples[:16000], (0, max(0, 16000-len(samples)))))
        raw = envelope_features(np.array(audio), envelope_filters(centers))
        expected = np.clip((raw-data["lo"]) / np.maximum(data["hi"]-data["lo"], 1e-6), 0, 1).astype("float32")
        expected = np.round(expected * 63) / 63 * 5
        np.testing.assert_array_equal(expected, data["X"][ids])
        print(label, "all 38908 split/name/class IDs match baseline; 60 sampled WAV features match exactly")

if __name__ == "__main__":
    main()
