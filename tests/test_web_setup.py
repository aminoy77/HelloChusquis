import json
import os
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlsplit, parse_qs
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch

from web.setup import run_setup_frontend, save_provider_config, setup_state


class WebSetupTest(unittest.TestCase):
    def test_saving_provider_keeps_existing_entries_and_masks_keys(self):
        stored = []
        config = {
            "providers": [{
                "name": "Groq",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": "old-secret",
                "model": "llama-3.3-70b-versatile",
                "priority": 1,
            }],
            "settings": {"memory_retention_days": 14},
            "agent": {"system_prompt": "x" * 120},
        }
        payload = {
            "provider": "OpenAI",
            "api_key": "new-secret",
            "model": "gpt-4o-mini",
        }
        with tempfile.TemporaryDirectory() as home:
            with patch("web.setup.Path.home", return_value=Path(home)), patch(
                "web.setup._save_config_securely", side_effect=lambda updated: stored.append(updated)
            ):
                updated = save_provider_config(config, payload)

        self.assertEqual(len(updated["providers"]), 2)
        self.assertEqual(updated["providers"][0]["api_key"], "old-secret")
        self.assertEqual(updated["providers"][1]["api_key"], "new-secret")
        self.assertEqual(updated["settings"]["memory_retention_days"], 14)
        self.assertNotIn("old-secret", json.dumps(setup_state(updated)))
        self.assertNotIn("new-secret", json.dumps(setup_state(updated)))
        self.assertEqual(stored, [updated])

    def test_existing_key_is_kept_when_editing_model(self):
        config = {
            "providers": [{
                "name": "OpenAI",
                "base_url": "https://api.openai.com/v1",
                "api_key": "keep-this-key",
                "model": "gpt-4o",
                "priority": 1,
            }]
        }
        with tempfile.TemporaryDirectory() as home:
            with patch("web.setup.Path.home", return_value=Path(home)), patch(
                "web.setup._save_config_securely"
            ):
                updated = save_provider_config(
                    config, {"provider": "OpenAI", "api_key": "", "model": "gpt-4.1"}
                )
        self.assertEqual(len(updated["providers"]), 1)
        self.assertEqual(updated["providers"][0]["api_key"], "keep-this-key")
        self.assertEqual(updated["providers"][0]["model"], "gpt-4.1")

    def test_key_required_and_provider_is_allowlisted(self):
        with self.assertRaisesRegex(ValueError, "API key"):
            save_provider_config({}, {"provider": "OpenAI", "api_key": "", "model": "gpt-4o"})
        with self.assertRaisesRegex(ValueError, "provider"):
            save_provider_config({}, {"provider": "https://attacker.invalid", "api_key": "x", "model": "x"})

    def test_local_frontend_saves_configuration(self):
        with tempfile.TemporaryDirectory() as home:
            opened = threading.Event()
            urls = []
            result = []
            errors = []

            def open_browser(url):
                urls.append(url)
                opened.set()
                return True

            def launch():
                try:
                    result.append(run_setup_frontend())
                except Exception as exc:
                    errors.append(exc)

            with patch.dict(os.environ, {"HOME": home}), patch("web.setup.webbrowser.open", side_effect=open_browser):
                thread = threading.Thread(target=launch, daemon=True)
                thread.start()
                try:
                    self.assertTrue(opened.wait(5), "setup server did not start")
                    parts = urlsplit(urls[0])
                    token = parse_qs(parts.query)["token"][0]
                    base_url = f"{parts.scheme}://{parts.netloc}"
                    page = urlopen(urls[0], timeout=5).read().decode("utf-8")
                    self.assertIn("Connect your model.", page)
                    self.assertIn(f"/logo.png?token={token}", page)
                    self.assertNotIn("secret-test-key", page)

                    logo = urlopen(f"{base_url}/logo.png?token={token}", timeout=5)
                    self.assertEqual(logo.headers.get_content_type(), "image/png")
                    self.assertTrue(logo.read().startswith(b"\x89PNG\r\n\x1a\n"))
                    with self.assertRaises(HTTPError) as denied_logo:
                        urlopen(f"{base_url}/logo.png?token=invalid", timeout=5)
                    self.assertEqual(denied_logo.exception.code, 403)

                    headers = {"X-Setup-Token": token}
                    forged_host = Request(
                        f"{base_url}/api/state",
                        headers={**headers, "Host": "not-local.example"},
                    )
                    with self.assertRaises(HTTPError) as denied_host:
                        urlopen(forged_host, timeout=5)
                    self.assertEqual(denied_host.exception.code, 403)

                    state_request = Request(f"{base_url}/api/state", headers=headers)
                    state = urlopen(state_request, timeout=5).read().decode("utf-8")
                    self.assertNotIn('"api_key":', state)
                    self.assertNotIn("secret-test-key", state)

                    models_body = json.dumps({
                        "provider": "OpenAI",
                        "api_key": "temporary-key",
                    }).encode("utf-8")
                    models_request = Request(
                        f"{base_url}/api/models",
                        data=models_body,
                        headers={
                            **headers,
                            "Origin": base_url,
                            "Content-Type": "application/json",
                        },
                        method="POST",
                    )
                    with patch("web.setup.fetch_available_models", return_value=["gpt-4o"]) as fetch_models:
                        models = json.loads(urlopen(models_request, timeout=5).read().decode("utf-8"))
                    self.assertEqual(models, {"models": ["gpt-4o"]})
                    fetch_models.assert_called_once_with(
                        "https://api.openai.com/v1", "temporary-key", provider_name="OpenAI"
                    )

                    body = json.dumps({
                        "provider": "OpenAI",
                        "api_key": "secret-test-key",
                        "model": "gpt-4o-mini",
                    }).encode("utf-8")
                    forged_origin = Request(
                        f"{base_url}/api/save",
                        data=body,
                        headers={
                            **headers,
                            "Origin": "http://not-local.example",
                            "Content-Type": "application/json",
                        },
                        method="POST",
                    )
                    with self.assertRaises(HTTPError) as denied_origin:
                        urlopen(forged_origin, timeout=5)
                    self.assertEqual(denied_origin.exception.code, 403)

                    save_request = Request(
                        f"{base_url}/api/save",
                        data=body,
                        headers={
                            **headers,
                            "Origin": base_url,
                            "Content-Type": "application/json",
                        },
                        method="POST",
                    )
                    response = urlopen(save_request, timeout=5).read().decode("utf-8")
                    self.assertEqual(json.loads(response), {"ok": True})
                finally:
                    if thread.is_alive() and urls:
                        parts = urlsplit(urls[0])
                        token = parse_qs(parts.query)["token"][0]
                        base_url = f"{parts.scheme}://{parts.netloc}"
                        fallback = Request(
                            f"{base_url}/api/save",
                            data=json.dumps({
                                "provider": "OpenAI", "api_key": "secret-test-key",
                                "model": "gpt-4o-mini",
                            }).encode("utf-8"),
                            headers={
                                "X-Setup-Token": token,
                                "Origin": base_url,
                                "Content-Type": "application/json",
                            },
                            method="POST",
                        )
                        try:
                            urlopen(fallback, timeout=3).close()
                        except Exception:
                            pass
                    thread.join(5)

            self.assertFalse(thread.is_alive(), "setup server did not stop after save")
            self.assertFalse(errors)
            self.assertEqual(result[0]["providers"][0]["api_key"], "secret-test-key")
            saved_path = os.path.join(home, ".hellochusquis", "config.yaml")
            self.assertTrue(os.path.isfile(saved_path))


if __name__ == "__main__":
    unittest.main()
