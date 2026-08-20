"""Regression tests for bounded vision-analysis image inputs."""

import unittest
from unittest.mock import patch

from core.media import ImageProcessor, _MAX_VISION_IMAGE_BYTES


class _OversizedBytes(bytes):
    def __len__(self) -> int:
        return _MAX_VISION_IMAGE_BYTES + 1


class TestMediaVisionInputBounds(unittest.TestCase):
    def test_vision_analysis_rejects_oversized_bytes_before_network_request(self):
        processor = ImageProcessor()
        with patch("httpx.post") as post:
            response = processor.analyze(_OversizedBytes(b""), api_key="test-key", model="gpt-4o")

        self.assertEqual(response, f"Error: image exceeds {_MAX_VISION_IMAGE_BYTES} bytes")
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
