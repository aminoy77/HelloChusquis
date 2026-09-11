"""doctor --live ping + config-shadow warning."""
import unittest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.setup import live_check_provider, find_config_shadows


def _resp(code=200):
    m = MagicMock()
    m.status_code = code
    return m


class TestLiveCheck(unittest.TestCase):
    def test_ok_on_200(self):
        with patch("httpx.Client") as client:
            client.return_value.__enter__.return_value.get.return_value = _resp(200)
            ok, detail, ms = live_check_provider(
                {"name": "X", "base_url": "https://x.ai/v1", "api_key": "k"})
        self.assertTrue(ok)
        self.assertGreaterEqual(ms, 0)

    def test_fail_on_connection_error(self):
        with patch("httpx.Client", side_effect=Exception("down")):
            ok, detail, ms = live_check_provider(
                {"name": "X", "base_url": "https://x.ai/v1", "api_key": "k"})
        self.assertFalse(ok)
        self.assertIn("down", detail)

    def test_fail_on_404(self):
        with patch("httpx.Client") as client:
            client.return_value.__enter__.return_value.get.return_value = _resp(404)
            ok, detail, ms = live_check_provider(
                {"name": "X", "base_url": "https://x.ai/v1", "api_key": "k"})
        self.assertFalse(ok)
        self.assertIn("404", detail)


class TestShadows(unittest.TestCase):
    def test_reports_shadowed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".hellochusquis").mkdir()
            (home / ".hellochusquis" / "config.yaml").write_text("a: 1")
            (home / "config.yaml").write_text("b: 2")
            with patch("core.setup.Path.home", return_value=home):
                active, shadowed = find_config_shadows()
        self.assertTrue(str(active).endswith(".hellochusquis/config.yaml"))
        self.assertEqual(len(shadowed), 1)

    def test_no_shadows_when_single(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            (home / ".hellochusquis").mkdir()
            (home / ".hellochusquis" / "config.yaml").write_text("a: 1")
            with patch("core.setup.Path.home", return_value=home):
                active, shadowed = find_config_shadows()
        self.assertEqual(shadowed, [])


if __name__ == "__main__":
    unittest.main()
