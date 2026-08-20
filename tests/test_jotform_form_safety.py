"""Regression tests for safe Jotform form identifiers."""

import unittest

from tools import jotform


class TestJotformFormSafety(unittest.TestCase):
    def test_form_identifier_is_a_positive_numeric_path_segment(self):
        self.assertEqual(jotform._form_id("231234567890123"), "231234567890123")
        for unsafe_id in ("../user", "231/submissions", "", "id\nX-Test: injected", "form_id"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    jotform._form_id(unsafe_id)


if __name__ == "__main__":
    unittest.main()
