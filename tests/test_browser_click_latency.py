"""Browser interaction latency regressions.

A click on an element far down the page used to take 30-60s: the human mouse
walked one CDP step per 3 pixels, so the number of round-trips grew with the
distance and the whole move was allowed to run for tens of seconds.
"""

import asyncio
import time
import unittest

from core.human_mouse import HumanMouse


class TestHumanMouseBoundedMovement(unittest.TestCase):
    def test_long_distance_move_stays_fast(self):
        mouse = HumanMouse(base_speed=0.3)
        moves = []

        async def on_move(x, y):
            moves.append((x, y))

        started = time.monotonic()
        asyncio.run(mouse.move_to((0, 0), (1200, 900), on_move=on_move))
        elapsed = time.monotonic() - started

        self.assertLess(elapsed, 5.0, "long mouse move must not take tens of seconds")
        self.assertLessEqual(len(moves), 60, "mouse walk must not issue unbounded CDP steps")
        self.assertGreater(len(moves), 1)

    def test_short_move_still_moves_to_target(self):
        mouse = HumanMouse()
        moves = []

        async def on_move(x, y):
            moves.append((x, y))

        asyncio.run(mouse.move_to((10, 10), (12, 12), on_move=on_move))

        self.assertEqual(moves[-1], (12, 12))


if __name__ == "__main__":
    unittest.main()
