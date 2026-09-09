"""Regression tests for safe Help Scout resource identifiers."""

import unittest

from tools import helpscout


class TestHelpScoutIdentifierSafety(unittest.TestCase):
    def test_helpscout_identifiers_are_positive_numeric_path_segments(self):
        self.assertEqual(helpscout._helpscout_id("12345", "conversation_id"), "12345")
        for unsafe_id in ("../mailboxes", "123/threads", "", "id\nX-Test: injected", "mailbox"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    helpscout._helpscout_id(unsafe_id, "conversation_id")

    def test_thread_types_and_statuses_are_constrained(self):
        self.assertEqual(helpscout._thread_type("NOTE"), "note")
        self.assertEqual(helpscout._conversation_status("PENDING"), "pending")
        with self.assertRaises(ValueError):
            helpscout._thread_type("reply&admin=true")
        with self.assertRaises(ValueError):
            helpscout._conversation_status("closed&force=true")


if __name__ == "__main__":
    unittest.main()
