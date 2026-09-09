"""Regression tests for bounded Calendly responses."""

import os
import unittest
from unittest.mock import patch

from tools import calendly


class _FakeResponse:
    status_code = 200

    def json(self):
        return {"collection": ["x" * 10_000]}


class TestCalendlyResponseBounds(unittest.TestCase):
    def test_list_events_bounds_remote_response_before_returning_it_to_the_agent(self):
        with patch.dict(os.environ, {"CALENDLY_API_TOKEN": "test-token"}, clear=False):
            with patch("tools.calendly.httpx.get", return_value=_FakeResponse()):
                result = calendly.run("list_events")
        self.assertTrue(result.success)
        self.assertLessEqual(len(result.output), 2000)


if __name__ == "__main__":
    unittest.main()
