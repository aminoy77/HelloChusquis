"""A timed-out browser task must be cancelled, not left running.

`do()` gives up after `timeout` seconds, but the handler kept executing in the
browser thread: a late navigation or click then hit a page the caller no longer
expects, and the health check saw "Execution context was destroyed".
"""

import asyncio
import queue
import time
import unittest
from types import SimpleNamespace

from tools.browser import PersistentBrowser


class _FakeAgent:
    def __init__(self, url="https://live.example/page"):
        self.state = SimpleNamespace(is_connected=True)
        self.page = SimpleNamespace(url=url)

    async def health_check(self):
        return True


class _LoopBrowser(PersistentBrowser):
    def __init__(self, tasks, handler):
        super().__init__()
        self._agent = _FakeAgent()
        self.tasks = list(tasks)
        self.handler = handler
        self.cancelled = False
        self.executed = 0

    async def _get_task_async(self):
        if self.tasks:
            return self.tasks.pop(0)
        self._stopped = True
        return ("__stop__", "", {}, time.monotonic() + 1)

    async def _execute_task(self, task_name, kwargs):
        if task_name:
            self.executed += 1
        try:
            return await self.handler()
        except asyncio.CancelledError:
            self.cancelled = True
            raise


class TestTaskTimeoutCancels(unittest.IsolatedAsyncioTestCase):
    async def test_slow_handler_is_cancelled_at_its_deadline(self):
        async def slow():
            await asyncio.sleep(5)
            return {"success": True}

        pb = _LoopBrowser([(1, "slow", {}, time.monotonic() + 2)], slow)
        await asyncio.wait_for(pb._task_processing_loop(), timeout=4)

        self.assertTrue(pb.cancelled)

    async def test_fast_handler_is_not_cancelled(self):
        async def fast():
            return {"success": True}

        pb = _LoopBrowser([(1, "fast", {}, time.monotonic() + 5)], fast)
        await asyncio.wait_for(pb._task_processing_loop(), timeout=3)

        self.assertFalse(pb.cancelled)
        self.assertEqual(pb.executed, 1)

    async def test_task_whose_caller_left_is_never_executed(self):
        async def fast():
            return {"success": True}

        pb = _LoopBrowser([(1, "fast", {}, time.monotonic() - 1)], fast)
        await asyncio.wait_for(pb._task_processing_loop(), timeout=3)

        self.assertEqual(pb.executed, 0)

    async def test_failure_reports_the_live_page_url(self):
        async def boom():
            return {"success": False, "error": "no visible element matched"}

        pb = _LoopBrowser([(1, "click", {}, time.monotonic() + 5)], boom)
        results = queue.Queue()
        pb._result_queues[1] = results
        await asyncio.wait_for(pb._task_processing_loop(), timeout=3)

        result = results.get_nowait()
        self.assertFalse(result["success"])
        self.assertEqual(result["url"], "https://live.example/page")


if __name__ == "__main__":
    unittest.main()
