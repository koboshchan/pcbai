"""Paid DC0 shift-register order and exact six-bit pulse-density frames."""
BLOCKS = (32, 40, 48, 56, 24, 16, 8, 0)
PHASES = tuple(sum(((i >> k) & 1) << (5 - k) for k in range(6))
               for i in range(63))


def validate_pixels(pixels):
    if not isinstance(pixels, (list, tuple)) or len(pixels) != 64:
        raise ValueError("pixels must contain 64 six-bit integers")
    if any(type(p) is not int or not 0 <= p <= 63 for p in pixels):
        raise ValueError("pixel values must be integers in 0..63")
    return pixels


def frame(pixels, phase):
    return bytes(sum((pixels[b + k] > phase) << k for k in range(8))
                 for b in BLOCKS)


def words(pixels):
    validate_pixels(pixels)
    out = []
    for phase in PHASES:
        f = frame(pixels, phase)
        out.extend((int.from_bytes(f[:4], "big"),
                    int.from_bytes(f[4:], "big")))
    return out


def score_voltage(adc_voltage):
    # 220k from score, 22k from 3V3, 22k to ground.
    return 21 * adc_voltage - 33
