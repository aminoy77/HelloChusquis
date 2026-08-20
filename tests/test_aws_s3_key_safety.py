"""Regression tests for safe AWS S3 object key path construction."""

import unittest

from tools import aws_s3


class TestAwsS3KeySafety(unittest.TestCase):
    def test_s3_object_key_is_encoded_without_ambiguous_path_segments(self):
        self.assertEqual(aws_s3._s3_key_path("reports/2026 final.csv"), "reports/2026%20final.csv")
        for unsafe_key in ("../secrets", "reports/../secrets", "", "report\nX-Test: injected"):
            with self.subTest(unsafe_key=unsafe_key):
                with self.assertRaises(ValueError):
                    aws_s3._s3_key_path(unsafe_key)


if __name__ == "__main__":
    unittest.main()
