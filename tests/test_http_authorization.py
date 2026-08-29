"""Tests that HTTP roles bound what a caller can reach and see."""

from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from api import main as api_main
from core.identity import IdentityStore, Permission, Role, legacy_owner
from web import server as web_server


def _request(principal, session="s1", host="test"):
    return SimpleNamespace(
        client=SimpleNamespace(host=host),
        headers={"x-hellochusquis-session": session},
        state=SimpleNamespace(principal=principal),
    )


class TestRoutePermissions(unittest.TestCase):
    def setUp(self):
        store = IdentityStore(":memory:")
        self.addCleanup(store.close)
        self.viewer, _ = store.create("viewer", Role.VIEWER)
        self.operator, _ = store.create("operator", Role.OPERATOR)
        self.owner, _ = store.create("owner", Role.OWNER)

    def test_viewer_cannot_chat_or_administer(self):
        for module in (api_main, web_server):
            for permission in (Permission.CHAT, Permission.MANAGE_RUNTIME, Permission.MANAGE_USERS):
                with self.subTest(module=module.__name__, permission=permission):
                    with self.assertRaises(HTTPException) as caught:
                        module.require_permission(_request(self.viewer), permission)
                    self.assertEqual(caught.exception.status_code, 403)

    def test_viewer_may_still_read_state(self):
        for module in (api_main, web_server):
            with self.subTest(module=module.__name__):
                self.assertEqual(
                    module.require_permission(_request(self.viewer), Permission.READ_STATE),
                    self.viewer,
                )

    def test_operator_cannot_manage_users_or_runtime(self):
        for permission in (Permission.MANAGE_USERS, Permission.MANAGE_RUNTIME):
            with self.subTest(permission=permission):
                with self.assertRaises(HTTPException) as caught:
                    api_main.require_permission(_request(self.operator), permission)
                self.assertEqual(caught.exception.status_code, 403)

    def test_owner_passes_every_gate(self):
        for permission in Permission:
            with self.subTest(permission=permission):
                api_main.require_permission(_request(self.owner), permission)

    def test_unauthenticated_request_is_rejected(self):
        anonymous = SimpleNamespace(client=None, headers={}, state=SimpleNamespace())
        with self.assertRaises(HTTPException) as caught:
            api_main.require_permission(anonymous, Permission.READ_STATE)
        self.assertEqual(caught.exception.status_code, 401)


class TestSessionIsolationAcrossPrincipals(unittest.TestCase):
    def test_same_session_header_from_two_principals_yields_two_agents(self):
        store = IdentityStore(":memory:")
        self.addCleanup(store.close)
        first, _ = store.create("first", Role.OPERATOR)
        second, _ = store.create("second", Role.OPERATOR)
        requested: list[tuple[str, Role]] = []

        def fake_get(session_id=None, role=None):
            requested.append((session_id, role))
            return SimpleNamespace()

        with patch.object(api_main.runtime, "get", fake_get):
            api_main._require_agent(_request(first, session="shared"))
            api_main._require_agent(_request(second, session="shared"))

        self.assertEqual(len(set(session for session, _ in requested)), 2)
        self.assertNotIn(first.id, requested[1][0])
        self.assertEqual(requested[0][1], Role.OPERATOR)

    def test_agent_session_key_carries_the_caller_role(self):
        captured: list = []

        def fake_get(session_id=None, role=None):
            captured.append(role)
            return SimpleNamespace()

        with patch.object(web_server.runtime, "get", fake_get):
            web_server._require_agent(_request(legacy_owner()))

        self.assertEqual(captured, [Role.OWNER])


if __name__ == "__main__":
    unittest.main()
