"""Regression tests for safe Todoist query construction."""

import unittest
from unittest.mock import patch

from tools import todoist


class _Response:
    def raise_for_status(self):
        return None

    def json(self):
        return []


class _Client:
    calls = []

    def __init__(self, **kwargs):
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def request(self, method, url, **kwargs):
        self.__class__.calls.append((method, url, kwargs))
        return _Response()


class TestTodoistQuerySafety(unittest.TestCase):
    def test_project_filter_is_passed_as_parameter(self):
        import asyncio

        with patch("tools.todoist.AsyncClient", _Client):
            asyncio.run(todoist.list_tasks("token", "project&label=all"))

        self.assertEqual(_Client.calls[0][0], "GET")
        self.assertEqual(_Client.calls[0][1], "https://api.todoist.com/rest/v2/tasks")
        self.assertEqual(_Client.calls[0][2]["params"], {"project_id": "project&label=all"})


if __name__ == "__main__":
    unittest.main()
