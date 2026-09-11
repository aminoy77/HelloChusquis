"""Config precedence (managed home wins) + local models are live-only."""
import unittest
import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core import setup as setup_mod


def _write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class TestConfigPrecedence(unittest.TestCase):
    def test_managed_home_beats_home_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            _write(home / ".hellochusquis" / "config.yaml",
                   "providers: [{name: Managed, base_url: http://x/v1, api_key: k, model: m, priority: 1}]\n")
            _write(home / "config.yaml",
                   "providers: [{name: Stale, base_url: http://x/v1, api_key: k, model: m, priority: 1}]\n")
            with patch.object(setup_mod.Path, "home", return_value=home):
                config = setup_mod.ensure_config(interactive=False)
        self.assertEqual(config["providers"][0]["name"], "Managed")


class TestLocalModelsLiveOnly(unittest.TestCase):
    def _live(self, models):
        m = MagicMock()
        m.status_code = 200
        m.json.return_value = {"data": [{"id": x} for x in models]}
        m.raise_for_status.return_value = None
        return m

    def test_local_lists_only_live_models(self):
        with patch("httpx.Client") as client:
            client.return_value.__enter__.return_value.get.return_value = self._live(
                ["pulled-model:3b"])
            models = setup_mod.fetch_available_models(
                "http://localhost:11434/v1", "", provider_name="Ollama (local)")
        self.assertEqual(models, ["pulled-model:3b"])

    def test_local_down_lists_nothing(self):
        with patch("httpx.Client", side_effect=Exception("down")):
            models = setup_mod.fetch_available_models(
                "http://localhost:11434/v1", "", provider_name="Ollama (local)")
        self.assertEqual(models, [])

    def test_remote_still_merges_catalog(self):
        with patch("httpx.Client") as client:
            client.return_value.__enter__.return_value.get.return_value = self._live(
                ["live-model"])
            models = setup_mod.fetch_available_models(
                "https://api.groq.com/openai/v1", "k", provider_name="Groq")
        self.assertIn("live-model", models)
        self.assertIn("llama-3.3-70b-versatile", models)


if __name__ == "__main__":
    unittest.main()
