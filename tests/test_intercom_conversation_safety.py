"""Regression tests for safe Intercom conversation identifiers."""

import unittest

from tools import intercom


class TestIntercomConversationSafety(unittest.TestCase):
    def test_conversation_identifier_is_a_single_safe_path_segment(self):
        self.assertEqual(intercom._conversation_id("conv_01HZX2Q9"), "conv_01HZX2Q9")
        for unsafe_id in ("../contacts", "conv_1/reply", "", "id\nX-Test: injected"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    intercom._conversation_id(unsafe_id)

    def test_filters_and_message_types_are_constrained(self):
        self.assertEqual(intercom._conversation_state("OPEN"), "open")
        self.assertEqual(intercom._message_type("NOTE"), "note")
        for unsafe_state in ("open&admin=true", "all"):
            with self.subTest(unsafe_state=unsafe_state):
                with self.assertRaises(ValueError):
                    intercom._conversation_state(unsafe_state)
        for unsafe_message_type in ("comment&role=admin", "reply"):
            with self.subTest(unsafe_message_type=unsafe_message_type):
                with self.assertRaises(ValueError):
                    intercom._message_type(unsafe_message_type)


if __name__ == "__main__":
    unittest.main()
