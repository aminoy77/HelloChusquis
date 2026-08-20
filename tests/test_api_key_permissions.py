"""Local API key storage permission tests."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from api import main as api_main
from web import server as web_server


class TestApiKeyPermissions(unittest.TestCase):
    def _assert_mode(self, path: Path, expected: int):
        self.assertEqual(path.stat().st_mode & 0o777, expected)

    def test_api_key_creation_uses_owner_only_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            key_dir = Path(directory) / "keys"
            key_file = key_dir / "api_key.txt"
            with patch.dict(os.environ, {}, clear=False), patch.object(api_main, "API_KEY_DIR", key_dir), patch.object(
                api_main, "API_KEY_FILE", key_file
            ):
                os.environ.pop("HELLOCHUSQUIS_API_KEY", None)
                api_main._load_or_generate_api_key()

            self._assert_mode(key_dir, 0o700)
            self._assert_mode(key_file, 0o600)

    def test_web_key_loader_repairs_existing_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            key_dir = Path(directory) / "keys"
            key_dir.mkdir(mode=0o755)
            key_file = key_dir / "api_key.txt"
            key_file.write_text("existing-key\n")
            os.chmod(key_file, 0o644)
            with patch.dict(os.environ, {}, clear=False), patch.object(web_server, "_AUTH_DIR", key_dir), patch.object(
                web_server, "_AUTH_KEY_FILE", key_file
            ):
                os.environ.pop("HELLOCHUSQUIS_API_KEY", None)
                self.assertEqual(web_server._load_or_create_api_key(), "existing-key")

            self._assert_mode(key_dir, 0o700)
            self._assert_mode(key_file, 0o600)

    def test_public_auth_check_does_not_reveal_local_key_path(self):
        response = TestClient(web_server.app).get("/auth/check")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(str(web_server._AUTH_KEY_FILE), response.json()["key_hint"])
        self.assertNotIn(str(Path.home()), response.json()["key_hint"])

    def test_web_start_does_not_log_the_api_key(self):
        with patch.object(web_server, "AUTH_ENABLED", True), patch.object(
            web_server.logger, "info"
        ) as info, patch.object(web_server.uvicorn, "run"):
            web_server.start()

        self.assertNotIn(web_server.REQUIRED_API_KEY, str(info.call_args))


if __name__ == "__main__":
    unittest.main()
