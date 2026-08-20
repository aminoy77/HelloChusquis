"""Regression tests for safe, usable QuickBooks integration requests."""

import os
import unittest
from unittest.mock import patch

from tools import quickbooks


class _Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {"QueryResponse": {"Customer": []}}


class _Client:
    def __init__(self):
        self.get_calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def get(self, url, **kwargs):
        self.get_calls.append((url, kwargs))
        return _Response()


class TestQuickBooksIntegrationSecurity(unittest.IsolatedAsyncioTestCase):
    async def test_customer_query_uses_company_url_bounded_client_and_numeric_limit(self):
        client = _Client()
        with (
            patch.dict(os.environ, {"QUICKBOOKS_COMPANY_ID": "12345"}, clear=True),
            patch("tools.quickbooks.AsyncClient", return_value=client) as async_client,
        ):
            result = await quickbooks.get_customers("test-token", max_results="1 OR 1=1")

        self.assertEqual(result, {"QueryResponse": {"Customer": []}})
        self.assertEqual(
            client.get_calls[0][0],
            "https://quickbooks.api.intuit.com/v3/company/12345/query",
        )
        self.assertEqual(
            client.get_calls[0][1]["params"]["query"],
            "SELECT Id, DisplayName FROM Customer MAXRESULTS 10",
        )
        self.assertEqual(async_client.call_args.kwargs["timeout"], quickbooks.QUICKBOOKS_TIMEOUT_SECONDS)
        self.assertFalse(async_client.call_args.kwargs["follow_redirects"])


if __name__ == "__main__":
    unittest.main()
