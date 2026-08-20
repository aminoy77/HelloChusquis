"""Regression tests for Trello API credential construction."""

import unittest

from tools import trello


class TestTrelloCredentials(unittest.TestCase):
    def test_api_parameters_require_a_real_key(self):
        self.assertEqual(trello._auth_params("real-key", "token"), {"key": "real-key", "token": "token"})
        with self.assertRaises(ValueError):
            trello._auth_params("key", "token")


if __name__ == "__main__":
    unittest.main()
