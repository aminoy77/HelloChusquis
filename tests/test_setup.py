"""Tests for is_complex from main.py."""
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import is_complex


class TestIsComplex(unittest.TestCase):
    """Test is_complex decision logic."""

    def test_simple_greeting(self):
        """'hola' is in FORCE_SIMPLE_KEYWORDS → always False."""
        self.assertFalse(is_complex("hola"))

    def test_informe_completo(self):
        """'informe' is in FORCE_PLAN_KEYWORDS → always True."""
        self.assertTrue(is_complex("informe completo"))

    def test_short_message(self):
        """<= 5 words, no complex keywords → False."""
        self.assertFalse(is_complex("short"))

    def test_many_words(self):
        """50 words (>10) → True."""
        text = " ".join(["word"] * 50)
        self.assertTrue(is_complex(text))

    def test_hello_simple(self):
        """'hello' in FORCE_SIMPLE_KEYWORDS → False."""
        self.assertFalse(is_complex("hello"))

    def test_analyze_keyword(self):
        """'analyze' in FORCE_PLAN_KEYWORDS → True."""
        self.assertTrue(is_complex("analyze this code please"))

    def test_boundary_five_words(self):
        """Exactly 5 words, no keywords → False."""
        self.assertFalse(is_complex("one two three four five"))

    def test_boundary_six_words(self):
        """6 words, no keywords → False (≤10 and not in simple/plan)."""
        self.assertFalse(is_complex("a b c d e f"))


if __name__ == "__main__":
    unittest.main()
