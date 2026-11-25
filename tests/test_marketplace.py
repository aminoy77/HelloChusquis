import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import core.marketplace as marketplace


class MarketplaceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name) / ".hellochusquis"
        patches = [
            patch.object(marketplace, "DEFAULT_HOME", self.home),
            patch.object(marketplace, "SKILLS_DIR", self.home / "skills"),
            patch.object(marketplace, "PLUGINS_DIR", self.home / "plugins"),
            patch.object(marketplace, "MCP_CONFIG", self.home / "mcp.json"),
        ]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)

    def tearDown(self):
        self.tmp.cleanup()

    def test_catalog_has_supported_items(self):
        items = marketplace.load_catalog()
        self.assertEqual({"skill", "plugin", "mcp"}, {item["kind"] for item in items})

    def test_install_and_uninstall_skill(self):
        marketplace.install_item("caveman")
        item = marketplace.get_item("caveman")
        self.assertTrue(marketplace.is_installed(item))
        marketplace.uninstall_item("caveman")
        self.assertFalse(marketplace.is_installed(item))

    def test_install_and_uninstall_plugin(self):
        marketplace.install_item("slack")
        item = marketplace.get_item("slack")
        self.assertTrue(marketplace.is_installed(item))
        marketplace.uninstall_item("slack")
        self.assertFalse(marketplace.is_installed(item))

    def test_reject_unknown_item(self):
        with self.assertRaises(marketplace.MarketplaceError):
            marketplace.install_item("../bad")


if __name__ == "__main__":
    unittest.main()
