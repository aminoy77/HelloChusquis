"""Audit #5: run_quick_setup must not crash for non-OAuth providers."""

import unittest
from unittest.mock import patch


class TestQuickSetup(unittest.TestCase):
    def test_non_oauth_provider_builds_config(self):
        from core import setup
        provider = {"name": "Groq", "base_url": "https://api.groq.com/openai/v1",
                    "requires_key": True, "oauth": False,
                    "models": ["llama-3.3-70b-versatile"]}
        with patch.object(setup, "pick_provider", return_value=provider), \
             patch.object(setup, "_prompt_api_key", return_value="gsk_test"), \
             patch.object(setup, "pick_model", return_value="llama-3.3-70b-versatile"), \
             patch.object(setup, "_save_config_securely", return_value="/tmp/c.yaml") as save, \
             patch.object(setup, "_check_providers_valid", return_value=None), \
             patch("pathlib.Path.home") as home:
            home.return_value = __import__("pathlib").Path("/tmp/fakehome")
            config = setup.run_quick_setup()
        self.assertEqual(config["providers"][0]["api_key"], "gsk_test")
        self.assertEqual(config["providers"][0]["model"], "llama-3.3-70b-versatile")
        save.assert_called_once()

    def test_oauth_failure_falls_back_to_ensure_config(self):
        from core import setup
        provider = {"name": "X", "base_url": "https://x", "requires_key": False,
                    "oauth": True}
        with patch.object(setup, "pick_provider", return_value=provider), \
             patch.object(setup, "login_provider", return_value=None), \
             patch.object(setup, "ensure_config", return_value={"ok": True}) as ec:
            config = setup.run_quick_setup()
        self.assertEqual(config, {"ok": True})
        ec.assert_called_once()


if __name__ == "__main__":
    unittest.main()
