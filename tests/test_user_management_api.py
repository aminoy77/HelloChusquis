"""Owner-only user management endpoints."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException

from api import main as api_main
from core.identity import Role, legacy_owner, reset_default_store


def _request(principal, host="10.0.0.1"):
    return SimpleNamespace(
        client=SimpleNamespace(host=host),
        headers={"x-hellochusquis-session": "admin"},
        state=SimpleNamespace(principal=principal),
    )


class TestUserManagementEndpoints(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patcher = patch.dict(
            os.environ,
            {"HELLOCHUSQUIS_IDENTITY_DB": str(Path(tmp.name) / "identity.db")},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        reset_default_store()
        self.addCleanup(reset_default_store)
        self.owner = legacy_owner()

    def test_owner_can_create_list_and_revoke_users(self):
        created = api_main.create_user(
            api_main.CreateUserRequest(name="dana", role="operator"), _request(self.owner)
        )

        self.assertTrue(created["token"])
        self.assertEqual(created["user"]["role"], "operator")
        self.assertNotIn("token_hash", created["user"])

        listed = api_main.list_users(_request(self.owner))["users"]
        self.assertEqual([user["name"] for user in listed], ["dana"])

        revoked = api_main.revoke_user("dana", _request(self.owner))
        self.assertIsNotNone(revoked["user"]["revoked_at"])

    def test_revoked_token_no_longer_authenticates(self):
        token = api_main.create_user(
            api_main.CreateUserRequest(name="erin", role="operator"), _request(self.owner)
        )["token"]
        self.assertIsNotNone(api_main.authenticate(token))

        api_main.revoke_user("erin", _request(self.owner))

        self.assertIsNone(api_main.authenticate(token))

    def test_non_owner_cannot_manage_users(self):
        token = api_main.create_user(
            api_main.CreateUserRequest(name="frank", role="operator"), _request(self.owner)
        )["token"]
        operator = api_main.authenticate(token)
        self.assertEqual(operator.role, Role.OPERATOR)

        with self.assertRaises(HTTPException) as caught:
            api_main.list_users(_request(operator))

        self.assertEqual(caught.exception.status_code, 403)

    def test_invalid_role_or_name_is_a_client_error(self):
        for payload in (
            api_main.CreateUserRequest(name="gina", role="superuser"),
            api_main.CreateUserRequest(name="Bad Name!", role="operator"),
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(HTTPException) as caught:
                    api_main.create_user(payload, _request(self.owner))
                self.assertEqual(caught.exception.status_code, 400)


if __name__ == "__main__":
    unittest.main()
