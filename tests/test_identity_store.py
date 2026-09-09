"""Tests for principal storage, roles and token handling."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.identity import (
    IdentityError,
    IdentityStore,
    Permission,
    Role,
    authenticate_bearer,
    default_store,
    legacy_owner,
    parse_role,
    reset_default_store,
)


class TestIdentityStore(unittest.TestCase):
    def setUp(self):
        self.store = IdentityStore(":memory:")
        self.addCleanup(self.store.close)

    def test_created_principal_authenticates_with_its_token_only(self):
        principal, token = self.store.create("alice", Role.OPERATOR)

        self.assertEqual(self.store.authenticate(token), principal)
        self.assertIsNone(self.store.authenticate(token + "x"))
        self.assertIsNone(self.store.authenticate(""))

    def test_token_secret_is_never_persisted_in_plaintext(self):
        _, token = self.store.create("bob", Role.VIEWER)

        rows = self.store._conn.execute("SELECT * FROM principals").fetchall()
        stored = " ".join(str(value) for row in rows for value in tuple(row))
        self.assertNotIn(token, stored)

    def test_public_view_excludes_secret_material(self):
        principal, token = self.store.create("carol", Role.VIEWER)

        view = principal.public_view()
        self.assertNotIn(token, str(view))
        self.assertEqual(view["role"], "viewer")
        self.assertTrue(view["active"])

    def test_revoked_principal_can_no_longer_authenticate(self):
        _, owner_token = self.store.create("owner", Role.OWNER)
        _, token = self.store.create("dave", Role.OPERATOR)

        revoked = self.store.revoke("dave")

        self.assertFalse(revoked.is_active)
        self.assertIsNone(self.store.authenticate(token))
        self.assertIsNotNone(self.store.authenticate(owner_token))

    def test_last_active_owner_cannot_be_revoked(self):
        self.store.create("only-owner", Role.OWNER)

        with self.assertRaises(IdentityError):
            self.store.revoke("only-owner")

    def test_duplicate_and_invalid_names_are_rejected(self):
        self.store.create("erin", Role.VIEWER)

        with self.assertRaises(IdentityError):
            self.store.create("erin", Role.VIEWER)
        with self.assertRaises(IdentityError):
            self.store.create("Erin Smith", Role.VIEWER)
        with self.assertRaises(IdentityError):
            self.store.create("a", Role.VIEWER)

    def test_unknown_role_is_rejected(self):
        with self.assertRaises(IdentityError):
            parse_role("superuser")
        with self.assertRaises(IdentityError):
            self.store.create("frank", "superuser")


class TestRolePermissions(unittest.TestCase):
    def test_viewer_is_read_only(self):
        viewer, _ = IdentityStore(":memory:").create("viewer", Role.VIEWER)

        self.assertTrue(viewer.has(Permission.READ_STATE))
        for permission in (
            Permission.CHAT,
            Permission.APPROVE,
            Permission.MUTATING_TOOLS,
            Permission.MANAGE_RUNTIME,
            Permission.MANAGE_USERS,
        ):
            self.assertFalse(viewer.has(permission), permission)

    def test_operator_may_act_but_not_administer(self):
        operator, _ = IdentityStore(":memory:").create("operator", Role.OPERATOR)

        self.assertTrue(operator.has(Permission.CHAT))
        self.assertTrue(operator.has(Permission.APPROVE))
        self.assertTrue(operator.has(Permission.MUTATING_TOOLS))
        self.assertFalse(operator.has(Permission.MANAGE_USERS))
        self.assertFalse(operator.has(Permission.MANAGE_RUNTIME))

    def test_owner_has_every_permission(self):
        owner = legacy_owner()

        for permission in Permission:
            self.assertTrue(owner.has(permission), permission)


class TestBearerAuthentication(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        patcher = patch.dict(
            os.environ,
            {"HELLOCHUSQUIS_IDENTITY_DB": str(Path(self._tmp.name) / "identity.db")},
        )
        patcher.start()
        self.addCleanup(patcher.stop)
        reset_default_store()
        self.addCleanup(reset_default_store)

    def test_legacy_deployment_key_authenticates_as_owner(self):
        principal = authenticate_bearer("deployment-key", legacy_key="deployment-key")

        self.assertIsNotNone(principal)
        self.assertIs(principal.role, Role.OWNER)

    def test_unknown_and_empty_tokens_are_rejected(self):
        self.assertIsNone(authenticate_bearer("", legacy_key="deployment-key"))
        self.assertIsNone(authenticate_bearer("not-a-token", legacy_key="deployment-key"))

    def test_stored_principal_authenticates_through_the_default_store(self):
        _, token = default_store().create("grace", Role.OPERATOR)

        principal = authenticate_bearer(token, legacy_key="deployment-key")

        self.assertIsNotNone(principal)
        self.assertEqual(principal.name, "grace")
        self.assertIs(principal.role, Role.OPERATOR)


if __name__ == "__main__":
    unittest.main()
