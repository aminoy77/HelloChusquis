"""Regression tests for safe LinkedIn profile identifiers."""

import unittest

from tools import linkedin


class TestLinkedInProfileSafety(unittest.TestCase):
    def test_profile_identifier_is_constrained_to_one_safe_path_segment(self):
        self.assertEqual(linkedin._profile_id("person_01HZX2Q9"), "person_01HZX2Q9")
        self.assertEqual(linkedin._profile_id("me"), "me")
        for unsafe_id in ("../messages", "person_1?projection=admin", "", "id\nX-Test: injected"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    linkedin._profile_id(unsafe_id)

    def test_recipients_and_message_text_are_constrained(self):
        self.assertEqual(linkedin._recipient_id("urn:li:person:abc_123"), "urn:li:person:abc_123")
        self.assertEqual(linkedin._bounded_text("A concise message", "message", 8000), "A concise message")
        for invalid_recipient in ("recipient/other", "", "recipient\nX-Test: injected"):
            with self.subTest(invalid_recipient=invalid_recipient):
                with self.assertRaises(ValueError):
                    linkedin._recipient_id(invalid_recipient)
        with self.assertRaises(ValueError):
            linkedin._bounded_text("x" * 8001, "message", 8000)


if __name__ == "__main__":
    unittest.main()
