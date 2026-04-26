"""
Human Mouse Movement Module
Generates realistic, non-linear mouse movements for browser automation.
"""

import math
import random
import time
from typing import Tuple, List, Callable, Optional


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
        """
        Args:
            base_speed: Base movement speed (lower = slower, more human)
            variation: Random variation factor (0.0-1.0)
            bump_probability: Chance of micro-jumps during movement (0.0-1.0)
            circle_probability: Chance of circular micro-movements (0.0-1.0)
            wobble_strength: How much the path wobbles (0.0-1.0)
        """
        self.base_speed = base_speed
        self.variation = variation
        self.bump_probability = bump_probability
        self.circle_probability = circle_probability
        self.wobble_strength = wobble_strength

    def move_to(
        self,
        start: Tuple[int, int],
        end: Tuple[int, int],
        duration: float = None,
        steps: int = None,
        on_move: Optional[Callable[[int, int], None]] = None
    ):
        """
        Move mouse from start to end with human-like movement.

        Args:
            start: Starting (x, y) coordinates
            end: Ending (x, y) coordinates
            duration: Total movement time in seconds (auto-calculated if None)
            steps: Number of steps (auto-calculated if None)
            on_move: Callback function called with (x, y) after each micro-movement
        """
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        distance = math.sqrt(dx * dx + dy * dy)

        if distance < 5:
            if on_move:
                on_move(end[0], end[1])
            return

        # Calculate steps based on distance
        if steps is None:
            steps = max(int(distance / 3), 20)
        if duration is None:
            # Vary the speed
            speed = self.base_speed * (1 + random.uniform(-self.variation, self.variation))
            duration = distance / (100 * speed)

        step_duration = duration / steps

        # Generate waypoints with human imperfections
        waypoints = self._generate_waypoints(start, end, steps)

        # Execute the movement
        for i, (target_x, target_y) in enumerate(waypoints):
            if i > 0:
                # Add pause variation (humans don't move constantly)
                pause = random.uniform(0, step_duration * 0.3)
                if pause > 0.01:
                    time.sleep(pause)

            if on_move:
                on_move(int(target_x), int(target_y))
            else:
                self._move_mouse(int(target_x), int(target_y))

            # Small random delay between steps
            time.sleep(step_duration * random.uniform(0.8, 1.2))

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

            # Linear interpolation
            x = start[0] + dx * progress
            y = start[1] + dy * progress

            # Add wobble (slight perpendicular movement)
            wobble = self._add_wobble(dx, dy, steps, i)

            # Add micro-circular movements
            if random.random() < self.circle_probability:
                wobble += self._add_circle_movement(steps, i)

            # Add bumps (small jumps)
            if random.random() < self.bump_probability:
                wobble += self._add_bump()

            x += wobble[0]
            y += wobble[1]

            waypoints.append((x, y))

        waypoints.append(end)
        return waypoints

    def _add_wobble(self, dx: float, dy: float, steps: int, current_step: int) -> Tuple[float, float]:
        """Add subtle perpendicular wobble to simulate hand micro-adjustments."""
        if dx == 0 and dy == 0:
            return (0, 0)

        # Calculate perpendicular direction
        length = math.sqrt(dx * dx + dy * dy)
        perp_x = -dy / length
        perp_y = dx / length

        # Sinusoidal wobble with noise
        phase = current_step * random.uniform(0.3, 0.7)
        amplitude = self.wobble_strength * random.uniform(2, 5)

        wobble_x = perp_x * math.sin(phase) * amplitude
        wobble_y = perp_y * math.sin(phase) * amplitude

        return (wobble_x, wobble_y)

    def _add_circle_movement(self, steps: int, current_step: int) -> Tuple[float, float]:
        """Add small circular micro-movement."""
        # Random circle parameters
        radius = random.uniform(3, 12)
        rotations = random.choice([-1, 1]) * random.uniform(0.3, 0.8)
        phase = current_step * rotations * math.pi / (steps / 4)

        # Add time-based noise
        phase += random.uniform(-0.2, 0.2)

        circle_x = math.cos(phase) * radius - radius  # Start from center of circle
        circle_y = math.sin(phase) * radius

        return (circle_x, circle_y)

    def _add_bump(self) -> Tuple[float, float]:
        """Add a small jump/bump during movement."""
        bump_x = random.uniform(-8, 8)
        bump_y = random.uniform(-8, 8)
        return (bump_x, bump_y)

    def _move_mouse(self, x: int, y: int):
        """Platform-specific mouse movement. Override for different platforms."""
        import pyautogui
        pyautogui.moveTo(x, y, _pause=False)

    def click(
        self,
        x: int,
        y: int,
        button: str = "left",
        on_move: Optional[Callable[[int, int], None]] = None
    ):
        """Move to position and click with human-like timing."""
        # Get current position
        import pyautogui
        current_pos = pyautogui.position()

        # Move with human-like motion
        self.move_to(
            (current_pos.x, current_pos.y),
            (x, y),
            on_move=on_move
        )

        # Small delay before click (human reaction time)
        time.sleep(random.uniform(0.05, 0.15))

        # Human-like click (sometimes double-click, sometimes right-click variation)
        if random.random() < 0.02:  # 2% chance of double-click
            pyautogui.doubleClick(x, y, button=button, _pause=False)
        else:
            pyautogui.click(x, y, button=button, _pause=False)

        # Small pause after click
        time.sleep(random.uniform(0.05, 0.1))

    def scroll(self, clicks: int, x: int = None, y: int = None):
        """Human-like scroll with variable speed."""
        import pyautogui

        if x is not None and y is not None:
            pyautogui.moveTo(x, y, _pause=False)

        # Split scroll into smaller chunks with variable delays
        scroll_chunks = abs(clicks)
        direction = 1 if clicks > 0 else -1

        for _ in range(scroll_chunks):
            pyautogui.scroll(direction, _pause=False)
            # Variable delay between scroll chunks
            time.sleep(random.uniform(0.02, 0.08))

    def hover(self, x: int, y: int, duration: float = None):
        """Move to position and hover for human-like duration."""
        import pyautogui
        current_pos = pyautogui.position()

        self.move_to((current_pos.x, current_pos.y), (x, y))

        if duration is None:
            duration = random.uniform(0.3, 1.0)

        time.sleep(duration)

    def type_text(self, text: str, interval: float = None):
        """Type text with variable interval (more human-like)."""
        import pyautogui

        for char in text:
            pyautogui.typewrite(char, interval=interval or random.uniform(0.05, 0.15))

            # Occasional pause (like thinking)
            if random.random() < 0.05:
                time.sleep(random.uniform(0.1, 0.3))


class MacHumanMouse(HumanMouse):
    """Mac-specific implementation."""

    def _move_mouse(self, x: int, y: int):
        import pyautogui
        pyautogui.moveTo(x, y, _pause=False)


class WindowsHumanMouse(HumanMouse):
    """Windows-specific implementation."""

    def _move_mouse(self, x: int, y: int):
        import pyautogui
        pyautogui.moveTo(x, y, _pause=False)


def get_human_mouse() -> HumanMouse:
    """Factory function to get the appropriate HumanMouse for the current platform."""
    import platform
    system = platform.system()

    if system == "Darwin":
        return MacHumanMouse()
    elif system == "Windows":
        return WindowsHumanMouse()
    else:
        return HumanMouse()


# Preset configurations
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