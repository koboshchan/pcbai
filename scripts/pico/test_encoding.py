import unittest
from encoding import BLOCKS, PHASES, frame, words, validate_pixels, score_voltage


class EncodingTests(unittest.TestCase):
    def test_all_duties_exact(self):
        self.assertEqual(sorted(PHASES), list(range(63)))
        for value in range(64):
            planes = [frame([value]*64, phase) for phase in PHASES]
            self.assertEqual(sum(bool(p[0]&1) for p in planes), value)

    def test_all_walking_ones_actual_chain(self):
        # U1..U8 physical Q0..7 blocks, read from paid DC0 pad nets.
        chain = (0, 8, 16, 24, 56, 48, 40, 32)
        for pixel in range(64):
            values = [0]*64
            values[pixel] = 63
            payload = frame(values, 0)
            # Earliest byte reaches U8, last reaches U1.
            result = [0]*64
            for byte, start in zip(reversed(payload), chain):
                for bit in range(8):
                    result[start+bit] = (byte >> bit) & 1
            self.assertEqual(result, [int(p==pixel) for p in range(64)])

    def test_words_msb_first(self):
        values = [n for n in range(64)]
        packed = words(values)
        self.assertEqual(len(packed), 126)
        for n, phase in enumerate(PHASES):
            data = packed[2*n].to_bytes(4,"big")+packed[2*n+1].to_bytes(4,"big")
            self.assertEqual(data, frame(values, phase))

    def test_zero_and_full(self):
        self.assertEqual(frame([0]*64, 0), bytes(8))
        self.assertEqual(frame([63]*64, 62), bytes([255]*8))

    def test_invalid(self):
        for v in (None, [], [0]*63, [64]*64, [-1]*64, [True]*64, [1.2]*64):
            with self.assertRaises(ValueError):
                validate_pixels(v)

    def test_divider(self):
        self.assertAlmostEqual(score_voltage(33/21), 0)
        self.assertAlmostEqual(score_voltage((15+33)/21),15)

if __name__ == "__main__":
    unittest.main()
