"""Regression tests for bounded, progressing audio chunking."""

import unittest
from unittest.mock import patch

from core.media import AudioProcessor


class TestAudioChunkBounds(unittest.TestCase):
    def test_chunk_rejects_overlap_that_prevents_progress_before_processing(self):
        processor = AudioProcessor()
        with patch.object(processor, "get_duration_ms", return_value=0) as duration:
            with self.assertRaisesRegex(ValueError, "overlap_ms must be smaller"):
                processor.chunk(b"audio", chunk_duration_ms=1_000, overlap_ms=1_000)

        duration.assert_not_called()


if __name__ == "__main__":
    unittest.main()
