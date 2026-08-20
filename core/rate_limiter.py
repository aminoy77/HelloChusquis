"""Bounded, thread-safe in-memory sliding-window rate limiter."""

from __future__ import annotations

from collections.abc import Callable
import threading
import time


class RateLimiter:
    """Per-client sliding-window limiter with bounded in-memory cardinality."""

    def __init__(
        self,
        requests_per_minute: int = 30,
        *,
        max_clients: int = 10_000,
        cleanup_interval: float = 30.0,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if requests_per_minute < 1:
            raise ValueError("requests_per_minute must be at least 1")
        if max_clients < 1:
            raise ValueError("max_clients must be at least 1")
        if cleanup_interval <= 0:
            raise ValueError("cleanup_interval must be positive")
        self._window = 60.0
        self._limit = requests_per_minute
        self._max_clients = max_clients
        self._cleanup_interval = cleanup_interval
        self._clock = clock
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()
        self._stop_cleanup = threading.Event()
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    @property
    def client_count(self) -> int:
        """Return the number of tracked clients for diagnostics and tests."""
        with self._lock:
            return len(self._hits)

    def close(self) -> None:
        """Stop the cleanup worker when a limiter is no longer needed."""
        self._stop_cleanup.set()
        if self._cleanup_thread.is_alive():
            self._cleanup_thread.join(timeout=self._cleanup_interval + 0.1)

    def _cleanup_loop(self) -> None:
        while not self._stop_cleanup.wait(self._cleanup_interval):
            self._cleanup()

    def _cleanup(self) -> None:
        cutoff = self._clock() - self._window
        with self._lock:
            self._prune_expired_locked(cutoff)

    def _prune_expired_locked(self, cutoff: float) -> None:
        expired = [client for client, timestamps in self._hits.items() if not timestamps or timestamps[-1] <= cutoff]
        for client in expired:
            self._hits.pop(client, None)

    def _ensure_capacity_locked(self) -> None:
        if len(self._hits) < self._max_clients:
            return
        oldest_client = min(
            self._hits,
            key=lambda client: self._hits[client][-1] if self._hits[client] else float("-inf"),
        )
        self._hits.pop(oldest_client, None)

    def is_allowed(self, client: str) -> bool:
        """Record a request and return whether it fits the client's window."""
        now = self._clock()
        cutoff = now - self._window
        with self._lock:
            timestamps = [timestamp for timestamp in self._hits.get(client, []) if timestamp > cutoff]
            if timestamps and len(timestamps) >= self._limit:
                self._hits[client] = timestamps
                return False
            if not timestamps and client not in self._hits:
                self._prune_expired_locked(cutoff)
                self._ensure_capacity_locked()
            timestamps.append(now)
            self._hits[client] = timestamps
            return True

    def get_remaining(self, client: str) -> int:
        """Return remaining requests without creating tracking state for a new client."""
        cutoff = self._clock() - self._window
        with self._lock:
            timestamps = [timestamp for timestamp in self._hits.get(client, []) if timestamp > cutoff]
            if timestamps:
                self._hits[client] = timestamps
            else:
                self._hits.pop(client, None)
            return max(0, self._limit - len(timestamps))

    def get_retry_after(self, client: str) -> float:
        """Return seconds until the oldest request in the current window expires."""
        now = self._clock()
        cutoff = now - self._window
        with self._lock:
            timestamps = [timestamp for timestamp in self._hits.get(client, []) if timestamp > cutoff]
            if timestamps:
                self._hits[client] = timestamps
            else:
                self._hits.pop(client, None)
                return 0.0
            return timestamps[0] - cutoff + 0.1
