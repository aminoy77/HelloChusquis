"""Regression tests for safe Google Calendar event routes."""

import unittest

from tools import google_calendar


class TestGoogleCalendarEventSafety(unittest.TestCase):
    def test_event_identifier_is_constrained_to_one_safe_path_segment(self):
        self.assertEqual(google_calendar._event_id("evt_01HZX2Q9"), "evt_01HZX2Q9")
        for unsafe_id in ("../settings", "evt_1/instances", "", "id\nX-Test: injected"):
            with self.subTest(unsafe_id=unsafe_id):
                with self.assertRaises(ValueError):
                    google_calendar._event_id(unsafe_id)

    def test_list_limit_is_bounded_and_event_times_are_required(self):
        self.assertEqual(google_calendar._bounded_max_results(999999), 2500)
        self.assertEqual(google_calendar._bounded_max_results("invalid"), 10)
        self.assertEqual(google_calendar._event_datetime("2026-08-20T12:00:00Z", "start"), "2026-08-20T12:00:00Z")
        for invalid_time in ("", "2026-08-20T12:00:00Z\nX-Test: injected"):
            with self.subTest(invalid_time=invalid_time):
                with self.assertRaises(ValueError):
                    google_calendar._event_datetime(invalid_time, "start")


if __name__ == "__main__":
    unittest.main()
