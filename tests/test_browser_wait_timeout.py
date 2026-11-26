"""Browser wait helpers must not race their own inner timeout.

`wait_for_element(selector, timeout=N)` used the same N for the inner Playwright
wait and the outer task deadline, so the caller always got
"Task timed out after Ns" instead of a clean success/failure result.
"""

import unittest
from unittest.mock import patch

from tools import browser


class _FakeBrowser:
    def __init__(self):
        self.calls = []

    def do(self, task_name, timeout=60, **kwargs):
        self.calls.append((task_name, timeout, kwargs))
        return {"success": True}


class TestBrowserWaitTimeouts(unittest.TestCase):
    def test_wait_for_element_outer_timeout_exceeds_inner_wait(self):
        fake = _FakeBrowser()
        with patch.object(browser, "_ensure_browser", return_value=fake):
            browser.browser_wait_for_element("#result", timeout=5)

        task_name, outer_timeout, kwargs = fake.calls[0]
        self.assertEqual(task_name, "wait_for_element")
        self.assertEqual(kwargs["wait_timeout"], 5)
        self.assertGreater(outer_timeout, 5)

    def test_wait_for_navigation_outer_timeout_exceeds_inner_wait(self):
        fake = _FakeBrowser()
        with patch.object(browser, "_ensure_browser", return_value=fake):
            browser.browser_wait_for_navigation(timeout=5)

        task_name, outer_timeout, kwargs = fake.calls[0]
        self.assertEqual(task_name, "wait_for_navigation")
        self.assertEqual(kwargs["wait_timeout"], 5)
        self.assertGreater(outer_timeout, 5)

    def test_negative_timeout_is_clamped_and_keeps_outer_deadline_longer(self):
        fake = _FakeBrowser()
        with patch.object(browser, "_ensure_browser", return_value=fake):
            browser.browser_wait_for_element("#result", timeout=-5)

        _task_name, outer_timeout, kwargs = fake.calls[0]
        self.assertEqual(kwargs["wait_timeout"], 0)
        self.assertGreater(outer_timeout, 0)


if __name__ == "__main__":
    unittest.main()
