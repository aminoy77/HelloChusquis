"""
Human Mouse Movement Module — Async version.
Generates realistic, non-linear mouse movements for browser automation.
No pyautogui dependency. Uses Playwright page.mouse API exclusively.
"""

import asyncio
import math
import random
from typing import Tuple, List, Callable, Optional, Awaitable


class HumanMouse:
    """Generates human-like mouse movements with realistic imperfections."""

    def __init__(
        self,
        base_speed: float = 0.5,
        variation: float = 0.3,
        bump_probability: float = 0.2,
        circle_probability: float = 0.15,
        wobble_strength: float = 0.1
    ):
        self.base_speed = base_speed
        self.variation = variation
        self.bump_probability = bump_probability
        self.circle_probability = circle_probability
        self.wobble_strength = wobble_strength

    async def move_to(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        duration: float = None,
        steps: int = None,
        on_move: Optional[Callable[[int, int], Awaitable[None]]] = None
    ):
        """
        Move mouse from start to end with human-like movement.

        Args:
            start: Starting (x, y) coordinates
            end: Ending (x, y) coordinates
            duration: Total movement time in seconds (auto-calculated if None)
            steps: Number of steps (auto-calculated if None)
            on_move: Async callback called with (x, y) after each micro-movement
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 5:
            if on_move:
                await on_move(end[0], end[1])
            return

        if steps is None:
            steps = max(int(distance / 3), 20)
        if duration is None:
            speed = self.base_speed * (1 + random.uniform(-self.variation, self.variation))
            duration = distance / (100 * speed)

        step_duration = duration / steps

        waypoints = self._generate_waypoints(start, end, steps)

        for i, (target_x, target_y) in enumerate(waypoints):
            if i > 0:
                pause = random.uniform(0, step_duration * 0.3)
                if pause > 0.01:
                    await asyncio.sleep(pause)

            if on_move:
                await on_move(int(target_x), int(target_y))

            await asyncio.sleep(step_duration * random.uniform(0.8, 1.2))

    def _generate_waypoints(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        steps: int
    ) -> List[Tuple[float, float]]:
        """Generate waypoints with various human imperfections."""
        waypoints = [start]

        dx = end[0] - start[0]
        dy = end[1] - start[1]

        for i in range(1, steps):
            progress = i / steps

            x = start[0] + dx * progress
            y = start[1] + dy * progress

            wobble = self._add_wobble(dx, dy, steps, i)

            if random.random() < self.circle_probability:
                wobble = (
                    wobble[0] + self._add_circle_movement(steps, i)[0],
                    wobble[1] + self._add_circle_movement(steps, i)[1],
                )

            if random.random() < self.bump_probability:
                bump = self._add_bump()
                wobble = (wobble[0] + bump[0], wobble[1] + bump[1])

            x += wobble[0]
            y += wobble[1]

            waypoints.append((x, y))

        waypoints.append(end)
        return waypoints

    def _add_wobble(self, dx: float, dy: float, steps: int, current_step: int) -> Tuple[float, float]:
        """Add subtle perpendicular wobble to simulate hand micro-adjustments."""
        if dx == 0 and dy == 0:
            return (0, 0)

        length = math.sqrt(dx * dx + dy * dy)
        perp_x = -dy / length
        perp_y = dx / length

        phase = current_step * random.uniform(0.3, 0.7)
        amplitude = self.wobble_strength * random.uniform(2, 5)

        wobble_x = perp_x * math.sin(phase) * amplitude
        wobble_y = perp_y * math.sin(phase) * amplitude

        return (wobble_x, wobble_y)

    def _add_circle_movement(self, steps: int, current_step: int) -> Tuple[float, float]:
        """Add small circular micro-movement."""
        radius = random.uniform(3, 12)
        rotations = random.choice([-1, 1]) * random.uniform(0.3, 0.8)
        phase = current_step * rotations * math.pi / (steps / 4)
        phase += random.uniform(-0.2, 0.2)

        circle_x = math.cos(phase) * radius - radius
        circle_y = math.sin(phase) * radius

        return (circle_x, circle_y)

    def _add_bump(self) -> Tuple[float, float]:
        """Add a small jump/bump during movement."""
        return (random.uniform(-8, 8), random.uniform(-8, 8))

    async def click(
        self,
        x: int,
        y: int,
        button: str = "left",
        on_move: Optional[Callable[[int, int], Awaitable[None]]] = None,
        page_mouse=None,
    ):
        """Move to position and click with human-like timing."""
        import random

        async def noop_move(x, y):
            if page_mouse:
                await page_mouse.move(x, y)

        move_cb = on_move or noop_move

        # Small delay before click (human reaction time)
        await asyncio.sleep(random.uniform(0.05, 0.15))

        if page_mouse:
            if random.random() < 0.02:
                await page_mouse.dblclick(x, y, button=button)
            else:
                await page_mouse.click(x, y, button=button)

        await asyncio.sleep(random.uniform(0.05, 0.1))

    async def hover(
        self,
        x: int,
        y: int,
        duration: float = None,
        page_mouse=None,
    ):
        """Move to position and hover for human-like duration."""
        if page_mouse:
            await page_mouse.move(x, y)
        if duration is None:
            duration = random.uniform(0.3, 1.0)
        await asyncio.sleep(duration)

    async def type_text(
        self,
        text: str,
        page_keyboard=None,
    ):
        """Type text with variable interval (more human-like)."""
        for char in text:
            if page_keyboard:
                await page_keyboard.type(char)
            delay = random.uniform(0.03, 0.12)
            if random.random() < 0.05:
                delay += random.uniform(0.1, 0.3)
            await asyncio.sleep(delay)


# Preset configurations
def get_human_mouse() -> HumanMouse:
    """Default realistic human mouse."""
    return HumanMouse(
        base_speed=0.6,
        variation=0.3,
        bump_probability=0.2,
        circle_probability=0.15,
        wobble_strength=0.1
    )


def get_fast_human_mouse() -> HumanMouse:
    """Fast but still human-like movements."""
    return HumanMouse(
        base_speed=1.5,
        variation=0.2,
        bump_probability=0.1,
        circle_probability=0.1,
        wobble_strength=0.05
    )


def get_slow_human_mouse() -> HumanMouse:
    """Very slow, cautious human-like movements."""
    return HumanMouse(
        base_speed=0.2,
        variation=0.5,
        bump_probability=0.3,
        circle_probability=0.2,
        wobble_strength=0.15
    )


def get_cautious_human_mouse() -> HumanMouse:
    """Cautious movements with more pauses and wobbles."""
    return HumanMouse(
        base_speed=0.3,
        variation=0.4,
        bump_probability=0.25,
        circle_probability=0.2,
        wobble_strength=0.12
    )
