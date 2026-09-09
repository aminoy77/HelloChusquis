"""Regression tests for approval of Cloudinary state-changing actions."""

import unittest

from core.approvals import approval_reason


class TestCloudinaryApprovals(unittest.TestCase):
    def test_upload_requires_approval_before_data_leaves_the_agent(self):
        reason = approval_reason("cloudinary", {"action": "upload", "file": "/workspace/photo.png"})

        self.assertIsNotNone(reason)
        self.assertIn("Cloudinary", reason)

    def test_read_only_resource_listing_does_not_require_approval(self):
        self.assertIsNone(approval_reason("cloudinary", {"action": "list_resources"}))


if __name__ == "__main__":
    unittest.main()
