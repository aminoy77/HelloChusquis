"""Regression tests for safe, bounded Stripe HTTP requests."""

import asyncio
import unittest
from unittest.mock import patch

from tools import stripe


class _Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {"data": []}


class _AsyncClient:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []
        self.__class__.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def get(self, url, **kwargs):
        self.calls.append(("get", url, kwargs))
        return _Response()


class TestStripeNetworkBounds(unittest.TestCase):
    def setUp(self):
        _AsyncClient.instances.clear()

    def test_list_invoices_uses_a_bounded_parameter_and_safe_client(self):
        with patch("tools.stripe.AsyncClient", _AsyncClient):
            asyncio.run(stripe.list_invoices("sk_test", limit=999999))

        client = _AsyncClient.instances[0]
        self.assertEqual(client.kwargs, {"timeout": 30, "follow_redirects": False})
        self.assertEqual(
            client.calls,
            [
                (
                    "get",
                    "https://api.stripe.com/v1/invoices",
                    {"params": {"limit": 100}, "auth": ("sk_test", "")},
                )
            ],
        )


if __name__ == "__main__":
    unittest.main()
