"""Public version contract tests."""

import unittest

from api import main as api_main
from core.version import __version__
from web import server as web_server


class TestVersionContract(unittest.TestCase):
    def test_api_root_uses_shared_version(self):
        self.assertEqual(api_main.root()["version"], __version__)

    def test_api_and_web_health_use_shared_version(self):
        self.assertEqual(api_main.health_check()["version"], __version__)
        self.assertEqual(web_server.health_check()["version"], __version__)


if __name__ == "__main__":
    unittest.main()
