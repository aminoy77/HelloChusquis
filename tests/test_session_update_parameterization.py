"""Regression tests for fixed, parameterized session updates."""

import unittest

from core.session import SessionManager


class TestSessionUpdateParameterization(unittest.TestCase):
    def test_update_uses_fixed_coalesce_statement_and_preserves_optional_fields(self):
        manager = SessionManager(":memory:")
        session_id = manager.create_session("agent", title="original", model="model-a")
        traced: list[str] = []
        manager._ensure_connection().set_trace_callback(traced.append)
        try:
            self.assertTrue(manager.update_session(session_id, title="updated"))
            metadata = manager.get_session(session_id)
        finally:
            manager.close()

        updates = [statement for statement in traced if statement.startswith("UPDATE sessions SET")]
        self.assertEqual(len(updates), 1)
        self.assertIn("COALESCE", updates[0])
        self.assertEqual(metadata.title, "updated")
        self.assertEqual(metadata.model, "model-a")


if __name__ == "__main__":
    unittest.main()
