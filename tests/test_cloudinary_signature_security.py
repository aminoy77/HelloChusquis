"""Regression tests for Cloudinary request signature strength."""

import hashlib
import unittest

from tools.cloudinary import _sign


class TestCloudinarySignatureSecurity(unittest.TestCase):
    def test_signature_uses_sha256_for_supported_cloudinary_requests(self):
        params = {"api_key": "key", "timestamp": "123", "folder": "images"}
        expected_payload = "api_key=key&folder=images&timestamp=123secret"

        signature = _sign(params, "secret")

        self.assertEqual(signature, hashlib.sha256(expected_payload.encode()).hexdigest())
        self.assertEqual(len(signature), 64)


if __name__ == "__main__":
    unittest.main()
