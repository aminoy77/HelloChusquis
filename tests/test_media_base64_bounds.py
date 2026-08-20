"""Regression tests for bounded media base64 decoding."""

import unittest

from core.media import ImageProcessor, _MAX_BASE64_ENCODED_CHARS


class _OversizedText(str):
    def __len__(self) -> int:
        return _MAX_BASE64_ENCODED_CHARS + 1


class TestMediaBase64Bounds(unittest.TestCase):
    def test_decode_base64_rejects_oversized_input_before_decoding(self):
        with self.assertRaisesRegex(ValueError, "base64 input exceeds"):
            ImageProcessor.decode_base64(_OversizedText(""))


if __name__ == "__main__":
    unittest.main()
