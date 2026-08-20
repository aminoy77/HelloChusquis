"""Security regressions for scheduled webhook delivery."""

import unittest
from unittest.mock import patch

from core.cron import CronDelivery, CronJob, CronRunResult, DeliveryTarget


class TestCronWebhookSecurity(unittest.TestCase):
    def test_private_webhook_destination_is_blocked_before_request(self):
        target = DeliveryTarget(webhook_url="http://127.0.0.1:8080/metadata")
        job = CronJob(id="job-1", name="Scheduled task")
        result = CronRunResult(summary="done")

        with patch("httpx.post") as post:
            delivered = CronDelivery._deliver_webhook(target, job, result, "completed")

        self.assertFalse(delivered)
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
