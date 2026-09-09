"""Regression tests for bounded remote TTS audio responses."""

import unittest
from unittest.mock import patch

from core.voice import MAX_TTS_AUDIO_BYTES, OpenAITTS


class _OversizedResponse:
    headers = {"Content-Length": str(MAX_TTS_AUDIO_BYTES + 1)}

    def raise_for_status(self):
        return None

    def iter_content(self, chunk_size):
        raise AssertionError("oversized response body must not be consumed")

    def close(self):
        return None


class TestVoiceRemoteAudioBounds(unittest.TestCase):
    def test_openai_tts_rejects_oversized_response_before_body_consumption(self):
        provider = OpenAITTS(api_key="test-key")
        response = _OversizedResponse()

        with patch("core.voice.requests.post", return_value=response) as post:
            result = provider.synthesize("hello")

        self.assertFalse(result.success)
        self.assertIn("TTS audio exceeds", result.error)
        self.assertTrue(post.call_args.kwargs["stream"])


if __name__ == "__main__":
    unittest.main()
