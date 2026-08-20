"""Regression tests for Airtable actions exposed by the agent schema."""

import os
import unittest
from unittest.mock import patch

from tools import airtable


class _Response:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {"records": []}


class TestAirtableAgentContract(unittest.TestCase):
    @patch.dict(os.environ, {"AIRTABLE_API_TOKEN": "pat-test", "AIRTABLE_BASE_ID": "app12345678901234"}, clear=False)
    @patch("tools.airtable.httpx.get", return_value=_Response())
    def test_list_records_action_offered_by_agent_is_executable(self, get):
        result = airtable.run("list_records", table="Tasks")

        self.assertTrue(result.success)
        self.assertEqual(get.call_args.args[0], "https://api.airtable.com/v0/app12345678901234/Tasks")
        self.assertFalse(get.call_args.kwargs["follow_redirects"])


if __name__ == "__main__":
    unittest.main()
