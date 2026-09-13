"""Fase 3: higiene packaging/launch estática."""
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


class PackagingHygieneTest(unittest.TestCase):
    def test_dist_ignored(self):
        content = Path(".gitignore").read_text()
        self.assertIn("dist/", content.splitlines())

    def test_sitemap_valid(self):
        tree = ET.parse("sitemap.xml")
        locs = [e.text for e in tree.getroot().iter("{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
        self.assertIn("https://hellochusquis.dev/", locs)

    def test_no_stale_root_landing(self):
        self.assertFalse(Path("hellochusquis-landing.html").exists())

    def test_changelog_newest_first(self):
        import re
        versions = re.findall(r"^## (\d+\.\d+)", Path("CHANGELOG.md").read_text(), re.M)
        self.assertGreaterEqual(len(versions), 2)
        self.assertEqual(versions[0], "5.4")
