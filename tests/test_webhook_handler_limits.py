import unittest

from core.webhook_handler import WebhookEvent, WebhookHandler


class TestWebhookHandlerLimits(unittest.TestCase):
    def setUp(self):
        self.handler = WebhookHandler()
        self.handler._events = [
            WebhookEvent(str(index), "test", "event", {}, str(index))
            for index in range(3)
        ]

    def test_zero_and_negative_limits_return_no_events(self):
        self.assertEqual(self.handler.get_events(limit=0), [])
        self.assertEqual(self.handler.get_events(limit=-1), [])

    def test_limits_are_bounded_and_invalid_values_use_default(self):
        self.assertEqual(len(self.handler.get_events(limit=1000)), 3)
        self.assertEqual(len(self.handler.get_events(limit="invalid")), 3)


if __name__ == "__main__":
    unittest.main()
