"""Regression tests for safe Slack request construction."""

import os
import unittest
from unittest.mock import patch

from tools import slack


class _Response:
    status_code = 200

    def json(self):
        return {"ok": True, "channel": {"name": "general", "id": "C123", "member_count": 1, "topic": {}}}


class _Client:
    instances = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.calls = []
        self.closed = False
        self.__class__.instances.append(self)

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return _Response()

    def close(self):
        self.closed = True


class TestSlackRequestSafety(unittest.TestCase):
    def setUp(self):
        _Client.instances.clear()

    @patch.dict(os.environ, {"SLACK_BOT_TOKEN": "xoxb-test"}, clear=False)
    @patch("tools.slack.httpx.Client", _Client)
    def test_channel_lookup_uses_parameters_and_a_closed_safe_client(self):
        result = slack.run("get_channel", channel="#C123&limit=999999")

        client = _Client.instances[0]
        self.assertIn("Channel: #general", result)
        self.assertEqual(client.kwargs, {"timeout": 30, "follow_redirects": False})
        self.assertEqual(
            client.calls,
            [
                (
                    "https://slack.com/api/conversations.info",
                    {"headers": unittest.mock.ANY, "params": {"channel": "C123&limit=999999"}},
                )
            ],
        )
        self.assertTrue(client.closed)


if __name__ == "__main__":
    unittest.main()
