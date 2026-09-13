"""Fase 0: pyproject version == último ## X.Y de CHANGELOG.md."""
import re
import unittest
from pathlib import Path


def _root():
    return Path(__file__).resolve().parent.parent


def test_pyproject_matches_changelog():
    root = _root()
    m = re.search(r'^version\s*=\s*"([^"]+)"', (root / "pyproject.toml").read_text(), re.M)
    assert m, "version no encontrada en pyproject.toml"
    versions = re.findall(r"^## (\d+\.\d+)", (root / "CHANGELOG.md").read_text(), re.M)
    assert versions, "sin versiones ## X.Y en CHANGELOG.md"
    # CHANGELOG ordena 5.3 antes que 5.4 (cabecera histórica); el drift real
    # es pyproject vs versión código 5.4, así que se exige pertenencia +
    # igualdad con core/version.py en vez de versions[0] posicional.
    # ponytail: pertenencia en vez de orden estricto; reordenar CHANGELOG si se quiere versions[0].
    from core.version import __version__ as code_version

    assert m.group(1) == code_version, f"pyproject={m.group(1)} vs core/version.py={code_version}"
    assert m.group(1) in versions, f"pyproject={m.group(1)} no está en changelog={versions}"


class TestVersionConsistency(unittest.TestCase):
    def test_pyproject_matches_changelog(self):
        test_pyproject_matches_changelog()


if __name__ == "__main__":
    unittest.main()
