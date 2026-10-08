import json
import unittest
from presence import Window, amplitudes, classify, parse_sample, variation


def sample(seq=0):
    return {"type": "csi", "seq": seq, "first_word_invalid": False, "iq": [3, 4] * 64}


class PresenceTests(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_sample(json.dumps(sample())), sample())
        for value in ("boot log", "null", "[]", "{}"):
            self.assertIsNone(parse_sample(value))
        bad = sample()
        bad["iq"][0] = True
        self.assertIsNone(parse_sample(json.dumps(bad)))
        bad["iq"][0] = 128
        self.assertIsNone(parse_sample(json.dumps(bad)))

    def test_normalization_and_invalid_word(self):
        row = sample()
        expected = amplitudes(row)
        row["first_word_invalid"] = True
        row["iq"][:4] = [127] * 4
        self.assertEqual(amplitudes(row), expected)
        self.assertEqual(expected, [1.0] * 62)
        row["iq"] = [0] * 128
        self.assertIsNone(amplitudes(row))

    def test_variation(self):
        self.assertEqual(variation([[1, 1], [1, 1]]), 0)
        self.assertGreater(variation([[1, 2], [2, 1]]), 0)
        self.assertIsNone(variation([]))
        with self.assertRaises(ValueError):
            variation([[1], [1, 2]])

    def test_no_empty_claim(self):
        self.assertEqual(classify(None, 0.1), "uncertain")
        self.assertEqual(classify(0, 0.1), "uncertain")
        self.assertEqual(classify(1, None), "uncertain")
        self.assertIn("possible presence", classify(1, 0.1))

    def test_window_quality_and_staleness(self):
        window = Window()
        for i in range(501):
            window.add(sample(i), i / 50)
        self.assertEqual(window.score(10), 0)
        self.assertIsNone(window.score(11))
        window.add(sample(505), 10.02)
        self.assertIsNone(window.score(10.02))

    def test_gap_resets_window(self):
        window = Window()
        window.add(sample(0), 0)
        window.add(sample(1), 1)
        self.assertEqual(len(window.rows), 1)


if __name__ == "__main__":
    unittest.main()
