"""Resource-boundary tests for the HTTP rate limiter."""

import unittest

from core.rate_limiter import RateLimiter


class TestRateLimiterBounds(unittest.TestCase):
    def setUp(self):
        self.now = 1_000.0
        self.limiters = []

    def tearDown(self):
        for limiter in self.limiters:
            limiter.close()

    def _limiter(self, **kwargs):
        limiter = RateLimiter(
            cleanup_interval=60.0,
            clock=lambda: self.now,
            **kwargs,
        )
        self.limiters.append(limiter)
        return limiter

    def test_unique_clients_are_bounded_by_recent_activity(self):
        limiter = self._limiter(requests_per_minute=2, max_clients=2)

        self.assertTrue(limiter.is_allowed("first"))
        self.now += 1
        self.assertTrue(limiter.is_allowed("second"))
        self.now += 1
        self.assertTrue(limiter.is_allowed("third"))

        self.assertEqual(limiter.client_count, 2)
        self.assertNotIn("first", limiter._hits)
        self.assertIn("second", limiter._hits)
        self.assertIn("third", limiter._hits)

    def test_read_only_queries_do_not_allocate_new_client_state(self):
        limiter = self._limiter(requests_per_minute=2, max_clients=2)

        self.assertEqual(limiter.get_remaining("never-seen"), 2)
        self.assertEqual(limiter.get_retry_after("never-seen"), 0.0)
        self.assertEqual(limiter.client_count, 0)

    def test_expired_clients_are_removed_before_capacity_eviction(self):
        limiter = self._limiter(requests_per_minute=2, max_clients=1)
        self.assertTrue(limiter.is_allowed("expired"))
        self.now += 61

        self.assertTrue(limiter.is_allowed("fresh"))
        self.assertEqual(limiter.client_count, 1)
        self.assertNotIn("expired", limiter._hits)
        self.assertIn("fresh", limiter._hits)

    def test_invalid_limits_are_rejected(self):
        with self.assertRaises(ValueError):
            self._limiter(requests_per_minute=0)
        with self.assertRaises(ValueError):
            self._limiter(requests_per_minute=1, max_clients=0)

    def test_close_stops_cleanup_worker(self):
        limiter = self._limiter(requests_per_minute=1)
        limiter.close()
        self.assertFalse(limiter._cleanup_thread.is_alive())


if __name__ == "__main__":
    unittest.main()
