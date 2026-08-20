"""Stateful HTTP session header contract tests."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from api import main as api_main
from web import server as web_server


class TestSessionHeaderContract(unittest.TestCase):
    def test_api_rejects_missing_session_header(self):
        with self.assertRaises(HTTPException) as raised:
            api_main._session_id(SimpleNamespace(headers={}))

        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("required", raised.exception.detail)

    def test_web_rejects_missing_session_header(self):
        with self.assertRaises(HTTPException) as raised:
            web_server._session_id(SimpleNamespace(headers={}))

        self.assertEqual(raised.exception.status_code, 400)
        self.assertIn("required", raised.exception.detail)

    def test_valid_header_is_preserved(self):
        request = SimpleNamespace(headers={"x-hellochusquis-session": "client.1_A-2"})

        self.assertEqual(api_main._session_id(request), "client.1_A-2")
        self.assertEqual(web_server._session_id(request), "client.1_A-2")

    def test_same_header_uses_distinct_internal_api_and_web_scopes(self):
        request = SimpleNamespace(headers={"x-hellochusquis-session": "client.1_A-2"})
        with patch.object(api_main.runtime, "get") as api_get, patch.object(
            web_server.runtime, "get"
        ) as web_get:
            api_main._require_agent(request)
            web_server._require_agent(request)

        api_get.assert_called_once_with(session_id="api:client.1_A-2")
        web_get.assert_called_once_with(session_id="web:client.1_A-2")


if __name__ == "__main__":
    unittest.main()
