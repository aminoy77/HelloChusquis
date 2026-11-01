"""Security regressions for plugin file names."""

import unittest
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

