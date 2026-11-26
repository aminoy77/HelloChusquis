"""Security regressions for plugin file names."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import plugins


class TestPluginNameSecurity(unittest.TestCase):
    def test_plugin_name_validator_rejects_path_traversal_and_extensions(self):
        for name in ("../escape", "nested/plugin", "plugin.py", "", " valid"):
            with self.assertRaises(ValueError):
                plugins.validate_plugin_name(name)

    def test_plugin_download_urls_require_public_https_without_credentials(self):
        for url in (
            "http://example.com/plugin.py",
            "https://127.0.0.1/plugin.py",
            "https://token@example.com/plugin.py",
        ):
            with self.assertRaises(ValueError):
                plugins.validate_plugin_download_url(url)

    def test_load_plugins_runs_once_per_process(self):
        with tempfile.TemporaryDirectory() as tmp_dir, patch.object(
            plugins, "PLUGINS_DIR", Path(tmp_dir)
        ), patch.object(plugins, "_loaded_plugins", None), patch.object(
            plugins, "_registry", None
        ):
            plugin_file = Path(tmp_dir) / "once.py"
            plugin_file.write_text(
                "PLUGIN_NAME = 'once'\nRUNS = globals().get('RUNS', 0) + 1\n"
            )
            plugin_file.chmod(0o600)
            first = plugins.load_plugins()
            second = plugins.load_plugins()

            self.assertIs(first, second)
            self.assertEqual([p["name"] for p in first], ["once"])
            self.assertEqual(first[0]["run"], None)
