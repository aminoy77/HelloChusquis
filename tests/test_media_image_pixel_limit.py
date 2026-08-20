"""Regression tests for image decompression-bomb resource limits."""

import unittest
from unittest.mock import patch

from core.media import ImageMetadata, ImageProcessor, _MAX_IMAGE_PIXELS


class TestImagePixelLimit(unittest.TestCase):
    def test_resize_rejects_oversized_image_before_converter_runs(self):
        processor = ImageProcessor()
        width = 5_001
        height = (_MAX_IMAGE_PIXELS // width) + 1

        with (
            patch.object(processor, "probe", return_value=ImageMetadata(width=width, height=height)),
            patch("core.media._run") as command,
        ):
            with self.assertRaisesRegex(ValueError, "pixel limit"):
                processor.resize(b"untrusted-image")

        command.assert_not_called()


if __name__ == "__main__":
    unittest.main()
