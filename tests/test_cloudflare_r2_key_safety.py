"""Regression tests for safe Cloudflare R2 object key paths."""

import unittest

from tools import cloudflare_r2


class TestCloudflareR2KeySafety(unittest.TestCase):
    def test_r2_object_key_is_encoded_without_ambiguous_path_segments(self):
        self.assertEqual(cloudflare_r2._r2_key_path("reports/2026 final.csv"), "reports/2026%20final.csv")
        for unsafe_key in ("../secrets", "reports/../secrets", "", "report\nX-Test: injected"):
            with self.subTest(unsafe_key=unsafe_key):
                with self.assertRaises(ValueError):
                    cloudflare_r2._r2_key_path(unsafe_key)


if __name__ == "__main__":
    unittest.main()
