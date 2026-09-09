"""Security regressions for outbound webhook delivery."""

import unittest
from unittest.mock import patch

from tools.webhook import run


class TestWebhookSecurity(unittest.TestCase):
    def test_send_blocks_private_network_destinations_before_request(self):
        with patch("tools.webhook.httpx.request") as request:
            result = run("send", url="http://127.0.0.1:8080/private")

        self.assertIn("SSRF blocked", result)
        request.assert_not_called()

    def test_send_rejects_host_override_header_before_request(self):
        with patch("tools.webhook.httpx.request") as request:
            result = run(
                "send",
                url="https://example.test/hook",
                headers='{"Host": "internal.service"}',
            )

        self.assertIn("blocked header", result)
        request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
