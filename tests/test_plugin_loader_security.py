"""Regression tests for safe local plugin discovery."""

import os
from pathlib import Path
import stat
import tempfile
import unittest

from core.plugins import PluginLoader


class TestPluginLoaderSecurity(unittest.TestCase):
    def test_discovery_makes_managed_directory_private_and_keeps_safe_plugin(self):
        with tempfile.TemporaryDirectory() as directory:
            plugins_dir = Path(directory) / "plugins"
            plugins_dir.mkdir(mode=0o755)
            safe_plugin = plugins_dir / "safe.py"
            safe_plugin.write_text("PLUGIN_NAME = 'safe'\n", encoding="utf-8")
            os.chmod(safe_plugin, 0o644)

            candidates = PluginLoader(plugins_dir).discover()

            self.assertEqual(stat.S_IMODE(plugins_dir.stat().st_mode), 0o700)
            self.assertEqual([candidate.id_hint for candidate in candidates], ["safe"])

    def test_discovery_rejects_symlinked_and_group_writable_plugin_code(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plugins_dir = root / "plugins"
            plugins_dir.mkdir()
            target = root / "outside.py"
            target.write_text("raise RuntimeError('must not load')\n", encoding="utf-8")
            linked = plugins_dir / "linked.py"
            linked.symlink_to(target)
            writable = plugins_dir / "writable.py"
            writable.write_text("PLUGIN_NAME = 'writable'\n", encoding="utf-8")
            os.chmod(writable, 0o666)

            candidates = PluginLoader(plugins_dir).discover()

            self.assertEqual(candidates, [])


if __name__ == "__main__":
    unittest.main()
