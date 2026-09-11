"""Setup: custom localhost URLs normalize to /v1; local URLs skip keys."""
import unittest
import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.setup import _normalize_custom_base_url, _is_local_url


def _resp(code):
    m = MagicMock()
    m.status_code = code
    return m


class TestNormalizeCustomBaseUrl(unittest.TestCase):
    def test_appends_v1_when_only_v1_answers(self):
        def fake_get(url, **kwargs):
            return _resp(200 if url == "http://localhost:11434/v1/models" else 404)
        with patch("httpx.Client") as client:
            client.return_value.__enter__.return_value.get.side_effect = fake_get
            self.assertEqual(
                _normalize_custom_base_url("http://localhost:11434"),
                "http://localhost:11434/v1",
            )

    def test_keeps_url_when_root_answers(self):
        with patch("httpx.Client") as client:
            client.return_value.__enter__.return_value.get.return_value = _resp(200)
            self.assertEqual(
                _normalize_custom_base_url("http://localhost:11434"),
                "http://localhost:11434",
            )

    def test_keeps_url_when_server_down(self):
        with patch("httpx.Client", side_effect=Exception("down")):
            self.assertEqual(
                _normalize_custom_base_url("http://localhost:11434"),
                "http://localhost:11434",
            )


class TestIsLocalUrl(unittest.TestCase):
    def test_local(self):
        self.assertTrue(_is_local_url("http://localhost:11434/v1"))
        self.assertTrue(_is_local_url("http://127.0.0.1:1337/v1"))

    def test_remote(self):
        self.assertFalse(_is_local_url("https://api.groq.com/openai/v1"))


if __name__ == "__main__":
    unittest.main()
