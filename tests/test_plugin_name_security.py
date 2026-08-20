"""Security regressions for plugin file names."""

import unittest
from unittest.mock import patch

from core import builder, plugins
from core.registry import PluginRegistry


class TestPluginNameSecurity(unittest.TestCase):
    def test_plugin_name_validator_rejects_path_traversal_and_extensions(self):
        for name in ("../escape", "nested/plugin", "plugin.py", "", " valid"):
            with self.assertRaises(ValueError):
                plugins.validate_plugin_name(name)

    def test_builder_rejects_unsafe_name_before_generating_or_writing(self):
        with patch.object(builder, "research_api") as research:
            with self.assertRaises(ValueError):
                builder.build_plugin("example", "../escape", pool=None)

        research.assert_not_called()

    def test_registry_rejects_unsafe_name_before_download(self):
        registry = PluginRegistry()
        registry.remote = {"../escape": {"url": "https://example.test/plugin.py"}}

        self.assertEqual(registry.install("../escape"), "Invalid plugin name")


if __name__ == "__main__":
    unittest.main()
