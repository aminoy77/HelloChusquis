"""Regression tests for safe Greenhouse Job Board routes."""

import unittest

from tools import greenhouse


class TestGreenhouseBoardSafety(unittest.TestCase):
    def test_board_token_is_a_single_safe_path_segment(self):
        self.assertEqual(greenhouse._board_token("acme-careers"), "acme-careers")
        for unsafe_token in ("acme/jobs", "acme?content=true", "", "acme\nX-Test: injected"):
            with self.subTest(unsafe_token=unsafe_token):
                with self.assertRaises(ValueError):
                    greenhouse._board_token(unsafe_token)


if __name__ == "__main__":
    unittest.main()
