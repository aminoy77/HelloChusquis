"""Tests for core.functions — utility functions."""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.functions import (
    calculate,
    hash_string,
    validate_email,
    slugify,
    text_stats,
)


class TestCalculate(unittest.TestCase):
    """Test safe math expression evaluator.

    NOTE: calculate() uses ast.literal_eval, which only supports literals
    (numbers, strings, tuples, lists, dicts, booleans, None). It does NOT
    evaluate arithmetic operators. So "2+2" returns an error, not 4.
    """

    def test_literal_integer(self):
        result = calculate("42")
        self.assertEqual(result["result"], 42)

    def test_literal_float(self):
        result = calculate("3.14")
        self.assertEqual(result["result"], 3.14)

    def test_literal_negative(self):
        result = calculate("-7")
        self.assertEqual(result["result"], -7)

    def test_literal_float_negative(self):
        result = calculate("-3.14")
        self.assertEqual(result["result"], -3.14)

    def test_literal_parens_grouping(self):
        """Parentheses allowed in character set — single number in parens."""
        result = calculate("(42)")
        self.assertEqual(result["result"], 42)

    def test_arithmetic_expression_returns_error(self):
        """ast.literal_eval rejects binary operators."""
        result = calculate("2+2")
        self.assertIn("error", result)

    def test_invalid_characters(self):
        result = calculate("import os")
        self.assertIn("error", result)


class TestHashString(unittest.TestCase):
    """Verify hash output length."""

    def test_sha256_length(self):
        result = hash_string("hello", "sha256")
        self.assertEqual(len(result["hash"]), 64)
        self.assertEqual(result["algorithm"], "sha256")

    def test_md5_length(self):
        result = hash_string("hello", "md5")
        self.assertEqual(len(result["hash"]), 32)

    def test_unknown_algorithm(self):
        result = hash_string("hello", "bogus")
        self.assertIn("error", result)


class TestValidateEmail(unittest.TestCase):
    """Valid/invalid email validation."""

    def test_valid_email(self):
        result = validate_email("user@example.com")
        self.assertTrue(result["valid"])

    def test_valid_email_with_dots(self):
        result = validate_email("first.last@domain.co")
        self.assertTrue(result["valid"])

    def test_invalid_email_no_at(self):
        result = validate_email("userexample.com")
        self.assertFalse(result["valid"])

    def test_invalid_email_no_tld(self):
        result = validate_email("user@domain")
        self.assertFalse(result["valid"])

    def test_invalid_email_empty(self):
        result = validate_email("")
        self.assertFalse(result["valid"])


class TestSlugify(unittest.TestCase):
    """Convert text to URL-friendly slug."""

    def test_hello_world(self):
        result = slugify("Hello World")
        self.assertEqual(result["slug"], "hello-world")

    def test_special_chars(self):
        result = slugify("It's a Test!")
        self.assertEqual(result["slug"], "its-a-test")

    def test_multiple_spaces(self):
        result = slugify("  lots   of   spaces  ")
        self.assertEqual(result["slug"], "lots-of-spaces")


class TestTextStats(unittest.TestCase):
    """Verify word/char counts."""

    def test_basic_stats(self):
        result = text_stats("Hello World")
        self.assertEqual(result["words"], 2)
        self.assertEqual(result["length"], 11)
        self.assertEqual(result["uppercase"], 2)
        self.assertEqual(result["lowercase"], 8)

    def test_empty_string(self):
        result = text_stats("")
        self.assertEqual(result["words"], 0)
        self.assertEqual(result["length"], 0)

    def test_digits_counted(self):
        result = text_stats("abc 123")
        self.assertEqual(result["digits"], 3)


if __name__ == "__main__":
    unittest.main()
