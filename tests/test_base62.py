import unittest

from src.base62 import decode, encode


class Base62Tests(unittest.TestCase):
    def test_round_trip_boundaries(self):
        for number in (0, 1, 61, 62, 63, 3844, 2**128):
            with self.subTest(number=number):
                self.assertEqual(decode(encode(number)), number)

    def test_alphabet_order(self):
        self.assertEqual(encode(0), "0")
        self.assertEqual(encode(9), "9")
        self.assertEqual(encode(10), "a")
        self.assertEqual(encode(35), "z")
        self.assertEqual(encode(36), "A")
        self.assertEqual(encode(61), "Z")
        self.assertEqual(encode(62), "10")

    def test_encode_rejects_negative_or_non_integer(self):
        for value, error in ((-1, ValueError), ("1", TypeError), (True, TypeError)):
            with self.subTest(value=value):
                with self.assertRaises(error):
                    encode(value)

    def test_decode_rejects_empty_or_invalid_input(self):
        for value, error in (("", ValueError), ("abc!", ValueError), (62, TypeError)):
            with self.subTest(value=value):
                with self.assertRaises(error):
                    decode(value)


if __name__ == "__main__":
    unittest.main()
