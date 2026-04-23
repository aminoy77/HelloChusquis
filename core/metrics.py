from __future__ import annotations
import json
from dataclasses import dataclass
from typing import Any


@dataclass
class Metric:
    name: str
    value: float
    unit: str
    timestamp: float


class MetricsCollector:
    """Collect and track agent metrics."""

    def __init__(self):
        self.metrics: list[Metric] = []
        self._counters: dict[str, int] = {}
        self._gauges: dict[str, float] = {}

    def increment(self, name: str, value: int = 1):
        """Increment a counter."""
        self._counters[name] = self._counters.get(name, 0) + value

    def gauge(self, name: str, value: float):
        """Set a gauge value."""
        self._gauges[name] = value
        self.metrics.append(Metric(name=name, value=value, unit="gauge", timestamp=self._now()))

    def timing(self, name: str, value: float):
        """Record a timing."""
        self.metrics.append(Metric(name=name, value=value, unit="ms", timestamp=self._now()))

    def _now(self) -> float:
        import time
        return time.time()

    def get_counter(self, name: str) -> int:
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        return self._gauges.get(name, 0.0)

    def summary(self) -> dict:
        """Get metrics summary."""
        return {
            "counters": self._counters.copy(),
            "gauges": self._gauges.copy(),
            "total_metrics": len(self.metrics)
        }

    def reset(self):
        """Reset all metrics."""
        self.metrics.clear()
        self._counters.clear()
        self._gauges.clear()


# Singleton instance
_collector = None


def get_collector() -> MetricsCollector:
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector