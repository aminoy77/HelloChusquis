"""Regression tests for the feedback contract between web UI and HTTP endpoints."""

from pathlib import Path
import unittest

from api import main as api_main
from web import server as web_server


class TestWebFeedbackContract(unittest.TestCase):
    def test_web_buttons_use_feedback_values_accepted_by_both_http_surfaces(self):
        index_html = (Path(__file__).parent.parent / "web" / "index.html").read_text(
            encoding="utf-8"
        )

        for accepted_type in ("positive", "negative"):
            self.assertIn(f"sendFeedback('{accepted_type}'", index_html)
            self.assertEqual(web_server.FeedbackRequest(type=accepted_type).type, accepted_type)
            self.assertEqual(api_main.FeedbackRequest(type=accepted_type).type, accepted_type)

        self.assertNotIn("sendFeedback('up'", index_html)
        self.assertNotIn("sendFeedback('down'", index_html)
        self.assertIn("return true;", index_html)
        self.assertIn("return false;", index_html)
        self.assertIn("if (await sendFeedback('positive'", index_html)
        self.assertIn("if (await sendFeedback('negative'", index_html)
        self.assertIn("Could not record feedback", index_html)


if __name__ == "__main__":
    unittest.main()
