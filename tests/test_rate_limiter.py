"""Tests for core.rate_limiter — RateLimiter class."""
import unittest
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.rate_limiter import RateLimiter


class TestRateLimiterWithinLimit(unittest.TestCase):
    """Requests within limit should all be allowed."""

    def test_allowed_within_limit(self):
        rl = RateLimiter(requests_per_minute=30)
        ip = "127.0.0.1"
        for _ in range(5):
            self.assertTrue(rl.is_allowed(ip))

    def test_allowed_at_exact_limit(self):
        rl = RateLimiter(requests_per_minute=3)
        ip = "10.0.0.1"
        self.assertTrue(rl.is_allowed(ip))
        self.assertTrue(rl.is_allowed(ip))
        self.assertTrue(rl.is_allowed(ip))


class TestRateLimiterBlockedOverLimit(unittest.TestCase):
    """Requests exceeding limit should be blocked."""

    def test_blocked_over_limit(self):
        rl = RateLimiter(requests_per_minute=30)
        ip = "192.168.1.1"
        for _ in range(30):
            self.assertTrue(rl.is_allowed(ip))
        # 31st request blocked
        self.assertFalse(rl.is_allowed(ip))

    def test_different_ips_independent(self):
        rl = RateLimiter(requests_per_minute=2)
        rl.is_allowed("ip1")
        rl.is_allowed("ip1")
        self.assertFalse(rl.is_allowed("ip1"))
        # Different IP should still be allowed
        self.assertTrue(rl.is_allowed("ip2"))


class TestRateLimiterRetryAfter(unittest.TestCase):
    """retry_after should be > 0 when blocked."""

    def test_retry_after_positive_when_blocked(self):
        rl = RateLimiter(requests_per_minute=2)
        ip = "test"
        rl.is_allowed(ip)
        rl.is_allowed(ip)
        # Now blocked — retry_after should be > 0
        retry = rl.get_retry_after(ip)
        self.assertGreater(retry, 0)

    def test_retry_after_zero_when_allowed(self):
        rl = RateLimiter(requests_per_minute=10)
        ip = "fresh"
        retry = rl.get_retry_after(ip)
        self.assertEqual(retry, 0.0)


if __name__ == "__main__":
    unittest.main()
