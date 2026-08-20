"""Regression tests for secure persistence of provider configuration secrets."""

from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch

import yaml

from core import setup


class TestProviderConfigPermissions(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary_directory.name)
        self.home_patch = patch.object(setup.Path, "home", return_value=self.home)
        self.home_patch.start()

    def tearDown(self):
        self.home_patch.stop()
        self.temporary_directory.cleanup()

    @staticmethod
    def _config():
        return {
            "providers": [{"name": "Provider", "api_key": "top-secret"}],
            "settings": {},
            "agent": {},
        }

    def test_config_directory_and_file_are_owner_only(self):
        config_dir = self.home / ".hellochusquis"
        config_dir.mkdir()
        config_path = config_dir / "config.yaml"
        config_path.write_text("providers: []\n", encoding="utf-8")
        config_dir.chmod(0o755)
        config_path.chmod(0o644)

        written_path = setup._save_config_securely(self._config())

        self.assertEqual(written_path, config_path)
        self.assertEqual(stat.S_IMODE(config_dir.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(config_path.stat().st_mode), 0o600)
        self.assertEqual(yaml.safe_load(config_path.read_text(encoding="utf-8")), self._config())
        self.assertEqual(list(config_dir.glob(".config.*.tmp")), [])

    def test_failed_replace_removes_temporary_secret_file(self):
        config_dir = self.home / ".hellochusquis"
        with patch.object(setup.os, "replace", side_effect=OSError("simulated failure")):
            with self.assertRaises(OSError):
                setup._save_config_securely(self._config())

        self.assertFalse((config_dir / "config.yaml").exists())
        self.assertEqual(list(config_dir.glob(".config.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
