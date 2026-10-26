"""Fase 1: catálogo congelado hasta Fase 2. Descongelar = orden owner."""
import glob
import unittest

from core.setup import KNOWN_PROVIDERS


class CatalogFreezeTest(unittest.TestCase):
    def test_provider_count_frozen(self):
        self.assertEqual(len(KNOWN_PROVIDERS), 75)

    def test_tool_count_frozen(self):
        files = [f for f in glob.glob("tools/*.py") if not f.endswith("__init__.py")]
        self.assertEqual(len(files), 134)
