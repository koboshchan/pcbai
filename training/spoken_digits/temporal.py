"""Label-independent energy endpointing and pitch-preserving temporal pooling."""
import numpy as np

VAD_CONFIG = dict(sample_rate=16000, window_samples=320, hop_samples=160,
                  noise_quantile=0.2, noise_multiplier=4.0,
                  peak_fraction=0.04, absolute_power_floor=1e-7,
                  min_run_frames=3, margin_samples=480,
                  minimum_samples=1280, fallback="whole clip")

def voiced_bounds(audio):
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
        return 0, len(x)
    lo = max(0, int(starts[keep][0]) * 160 - 480)
    hi = min(len(x), int(ends[keep][-1] - 1) * 160 + 320 + 480)
    if hi - lo < 1280:
        mid = (lo + hi) // 2
        lo = min(max(0, mid - 640), len(x) - 1280)
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
