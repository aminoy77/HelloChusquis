"""Regression tests for safe Typeform form identifiers."""

import unittest

from tools import typeform


class TestTypeformFormSafety(unittest.TestCase):
    def test_form_identifier_is_a_single_safe_path_segment(self):
        self.assertEqual(typeform._form_id("abc123_DEF-09"), "abc123_DEF-09")
        for unsafe_id in ("../forms", "form/responses", "", "id\nX-Test: injected"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    typeform._form_id(unsafe_id)


if __name__ == "__main__":
    unittest.main()
