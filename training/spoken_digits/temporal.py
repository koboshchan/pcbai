"""Label-independent energy endpointing and pitch-preserving temporal pooling."""
import numpy as np

VAD_CONFIG = dict(sample_rate=16000, window_samples=320, hop_samples=160,
                  noise_quantile=0.2, noise_multiplier=4.0,
                  peak_fraction=0.04, absolute_power_floor=1e-7,
                  min_run_frames=3, margin_samples=480,
                  minimum_samples=1280, fallback="whole clip")

ALIGNMENT_LABELS = [base + suffix for base in ["4x16-alt", "8x8"]
                    for suffix in ["-trimmed", "-onset300", "-onset500", "-onset700"]]

def detected_region(audio):
    """20ms RMS-energy windows, 10ms hop; never use labels or dataset splits."""
    x = np.asarray(audio, dtype=np.float64)
    if x.shape != (16000,):
        raise ValueError("expected exactly 16000 mono samples")
    if not np.isfinite(x).all():
        raise ValueError("nonfinite audio")
    centered = x - x.mean()
    frames = np.lib.stride_tricks.sliding_window_view(centered, 320)[::160]
    energy = np.mean(frames * frames, axis=1)
    noise = np.quantile(energy, 0.2)
    peak = energy.max()
    threshold = max(4 * noise, 0.04 * peak, 1e-7)
    active = energy > threshold
    # Reject single clicks; retain every sustained region, including separated syllables.
    padded = np.r_[False, active, False].astype(int)
    starts = np.flatnonzero(np.diff(padded) == 1)
    ends = np.flatnonzero(np.diff(padded) == -1)
    keep = ends - starts >= 3
    if not np.any(keep):
        return None
    return int(starts[keep][0]) * 160, int(ends[keep][-1] - 1) * 160 + 320

def voiced_bounds(audio):
    region = detected_region(audio)
    if region is None:
        return 0, len(audio)
    lo = max(0, region[0] - 480)
    hi = min(len(audio), region[1] + 480)
    if hi - lo < 1280:
        mid = (lo + hi) // 2
        lo = min(max(0, mid - 640), len(audio) - 1280)
        hi = lo + 1280
    return lo, hi

def pool_interval(values, start, end, bins):
    """Exact fractional-cell mean in uniform relative-time bins on the last axis."""
    values = np.asarray(values)
    if not 0 <= start < end <= values.shape[-1]:
        raise ValueError("invalid pooling interval")
    edges = np.linspace(start, end, bins + 1)
    indexes = np.minimum(np.floor(edges).astype(int), values.shape[-1] - 1)
    cumulative = np.concatenate([np.zeros(values.shape[:-1] + (1,)),
                                 np.cumsum(values, axis=-1, dtype=np.float64)], axis=-1)
    integral = cumulative[..., indexes] + values[..., indexes] * (edges - indexes)
    return np.diff(integral, axis=-1) / np.diff(edges)

def alignment_bounds(audio, label):
    if label.endswith("-trimmed"):
        return voiced_bounds(audio)
    if "-onset" not in label:
        return 0, 16000
    duration_ms = int(label.rsplit("-onset", 1)[1])
    if duration_ms not in (300, 500, 700):
        raise ValueError("unsupported onset window")
    region = detected_region(audio)
    onset = 0 if region is None else region[0]
    return onset, onset + duration_ms * 16

def alignment_config(label):
    if label.endswith("-trimmed"):
        return {"type":"energy-VAD normalized-time pooling; no waveform pitch shift", **VAD_CONFIG}
    if "-onset" in label:
        return {"type":"fixed duration from detected onset; normalized-time pooling",
                "duration_ms":int(label.rsplit("-onset",1)[1]), "pre_margin_ms":0,
                "beyond_clip":"zero pad, never shift onset or shorten window",
                "no_detection_onset":0, **VAD_CONFIG, "margin_samples":0,
                "minimum_samples":None, "fallback":"onset zero, exact fixed duration"}
    return {"type":"fixed one-second bins"}
