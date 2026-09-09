"""Regression tests for safe Datadog metric query construction."""

import unittest
from unittest.mock import patch

from tools import datadog


class _Response:
    def raise_for_status(self):
        return None

    def json(self):
        return {"series": []}


class _AsyncClient:
    instances = []

    def __init__(self, **kwargs):
        self.calls = []
        self.__class__.instances.append(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _Response()


class TestDatadogQuerySafety(unittest.TestCase):
    def test_metric_query_is_passed_as_a_parameter(self):
        import asyncio

        with patch("tools.datadog.AsyncClient", _AsyncClient):
            asyncio.run(datadog.get_metrics("key", "avg:cpu{host:a&b}"))

        self.assertEqual(_AsyncClient.instances[0].calls[0][0], "https://api.datadoghq.com/api/v1/query")
        self.assertEqual(_AsyncClient.instances[0].calls[0][1]["params"], {"query": "avg:cpu{host:a&b}"})


if __name__ == "__main__":
    unittest.main()
