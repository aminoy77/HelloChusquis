"""Stateful HTTP session header contract tests."""

from types import SimpleNamespace
import unittest

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


if __name__ == "__main__":
    unittest.main()
