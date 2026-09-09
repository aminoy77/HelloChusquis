"""Regression tests for Salesforce CRM HTTP execution."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import enterprise


class TestSalesforceHttpSafety(unittest.TestCase):
    def test_list_objects_uses_bounded_http_client_without_redirects(self):
        response = SimpleNamespace(status_code=200, json=lambda: {"sobjects": []})
        with (
            patch.dict(
                "os.environ",
                {"SALESFORCE_TOKEN": "test-token", "SALESFORCE_INSTANCE": "example"},
                clear=True,
            ),
            patch("tools.enterprise.httpx.get", return_value=response) as get,
        ):
            result = enterprise.run("list_objects")

        self.assertEqual(result, "Objects:\n")
        self.assertEqual(get.call_args.kwargs["timeout"], enterprise.SALESFORCE_HTTP_TIMEOUT_SECONDS)
        self.assertFalse(get.call_args.kwargs["follow_redirects"])


if __name__ == "__main__":
    unittest.main()
