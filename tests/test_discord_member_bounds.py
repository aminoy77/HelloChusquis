"""Regression tests for bounded Discord member list requests."""

import unittest

from tools import discord


class TestDiscordMemberBounds(unittest.TestCase):
    def test_member_limit_is_bounded(self):
        self.assertEqual(discord._member_limit(-1), 1)
        self.assertEqual(discord._member_limit(10000), 1000)


if __name__ == "__main__":
    unittest.main()
