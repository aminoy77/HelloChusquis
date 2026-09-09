"""Regression tests for safe Salesforce SOQL query construction."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from tools import enterprise


class TestSalesforceQueryValidation(unittest.TestCase):
    def test_query_rejects_injected_sobject_before_network_request(self):
        with (
            patch.dict(
                "os.environ",
                {"SALESFORCE_TOKEN": "test-token", "SALESFORCE_INSTANCE": "example"},
                clear=True,
            ),
            patch("tools.enterprise.httpx.get") as get,
        ):
            result = enterprise.run("query", sobject="Account WHERE Name != ''")

        self.assertEqual(result, "Error: invalid Salesforce object")
        get.assert_not_called()

    def test_query_uses_default_valid_fields(self):
        response = SimpleNamespace(status_code=200, json=lambda: {"records": []})
        with (
            patch.dict(
                "os.environ",
                {"SALESFORCE_TOKEN": "test-token", "SALESFORCE_INSTANCE": "example"},
                clear=True,
            ),
            patch("tools.enterprise.httpx.get", return_value=response) as get,
        ):
            result = enterprise.run("query", sobject="Account")

        self.assertEqual(result, "")
        self.assertEqual(get.call_args.kwargs["params"]["q"], "SELECT Id, Name FROM Account LIMIT 10")


if __name__ == "__main__":
    unittest.main()
