"""Regression tests for bounded Cloudinary requests."""

import os
import unittest
from unittest.mock import patch

from tools import cloudinary


class _Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {"resources": []}


class TestCloudinaryNetworkBounds(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "CLOUDINARY_CLOUD_NAME": "demo-cloud",
            "CLOUDINARY_API_KEY": "key",
            "CLOUDINARY_API_SECRET": "secret",
        },
        clear=False,
    )
    @patch("tools.cloudinary.httpx.get", return_value=_Response())
    def test_resource_list_caps_results_and_disables_redirects(self, get):
        result = cloudinary.run("list_resources", max_results=999999)

        self.assertEqual(result, "[]")
        self.assertEqual(get.call_args.kwargs["params"]["max_results"], 100)
        self.assertFalse(get.call_args.kwargs["follow_redirects"])
        self.assertEqual(get.call_args.kwargs["timeout"], 30)

    @patch.dict(os.environ, {"CLOUDINARY_CLOUD_NAME": "bad/name", "CLOUDINARY_API_KEY": "key"}, clear=False)
    @patch("tools.cloudinary.httpx.get")
    def test_rejects_cloud_names_that_cannot_safely_form_a_url_path(self, get):
        result = cloudinary.run("list_resources")

        self.assertEqual(result, "Error: Invalid Cloudinary cloud name.")
        get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
