"""Regression tests for bounded Close CRM responses."""

import unittest
from unittest.mock import patch

from tools.close import CloseTool


class _FakeResponse:
    def json(self):
        return {"payload": "x" * 10_000}


class TestCloseResponseBounds(unittest.TestCase):
    def test_list_leads_bounds_remote_response_before_returning_it_to_the_agent(self):
        tool = CloseTool()
        tool.config = {"token": "test-token"}
        with patch("tools.close.httpx.get", return_value=_FakeResponse()):
            result = tool.run("list_leads")
        self.assertTrue(result.success)
        self.assertLessEqual(len(result.output), 2000)


if __name__ == "__main__":
    unittest.main()
