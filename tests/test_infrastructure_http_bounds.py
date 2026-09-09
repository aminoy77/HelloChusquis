"""Regression tests for bounded infrastructure provider HTTP calls."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import terraform


class TestInfrastructureHttpBounds(unittest.TestCase):
    def test_cloudflare_listing_uses_timeout_and_disables_redirects(self):
        response = SimpleNamespace(status_code=200, json=lambda: {"result": []})
        with (
            patch.dict("os.environ", {"CLOUDFLARE_TOKEN": "test-token"}, clear=True),
            patch("tools.terraform.httpx.get", return_value=response) as get,
        ):
            result = terraform.cloudflare("list_zones")

        self.assertEqual(result, "")
        self.assertEqual(get.call_args.kwargs["timeout"], terraform.INFRASTRUCTURE_HTTP_TIMEOUT_SECONDS)
        self.assertFalse(get.call_args.kwargs["follow_redirects"])

    def test_vercel_listing_uses_timeout_and_disables_redirects(self):
        response = SimpleNamespace(status_code=200, json=lambda: {"deployments": []})
        with (
            patch.dict("os.environ", {"VERCEL_TOKEN": "test-token"}, clear=True),
            patch("tools.terraform.httpx.get", return_value=response) as get,
        ):
            result = terraform.vercel("list")

        self.assertEqual(result, "")
        self.assertEqual(get.call_args.kwargs["timeout"], terraform.INFRASTRUCTURE_HTTP_TIMEOUT_SECONDS)
        self.assertFalse(get.call_args.kwargs["follow_redirects"])


if __name__ == "__main__":
    unittest.main()
