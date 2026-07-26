"""Simple in-memory rate limiter using sliding window."""
import time
import threading
from collections import defaultdict


class RateLimiter:
    """Per-IP sliding window rate limiter. Thread-safe."""

    def __init__(self, requests_per_minute: int = 30):
        self._window = 60  # seconds
        self._limit = requests_per_minute
        self._hits: dict[str, list[float]] = defaultdict(list)
        self._lock = threading.Lock()
        # Start cleanup thread (daemon = dies with process)
        t = threading.Thread(target=self._cleanup_loop, daemon=True)
        t.start()

    def _cleanup_loop(self):
        while True:
            time.sleep(30)
            self._cleanup()

    def _cleanup(self):
        now = time.time()
        cutoff = now - self._window
        with self._lock:
            expired = [ip for ip, ts in self._hits.items() if not ts or ts[-1] < cutoff]
            for ip in expired:
                del self._hits[ip]

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        cutoff = now - self._window
        with self._lock:
            self._hits[ip] = [t for t in self._hits[ip] if t > cutoff]
            if len(self._hits[ip]) >= self._limit:
                return False
            self._hits[ip].append(now)
            return True

    def get_remaining(self, ip: str) -> int:
        now = time.time()
        cutoff = now - self._window
        with self._lock:
            self._hits[ip] = [t for t in self._hits[ip] if t > cutoff]
            return max(0, self._limit - len(self._hits[ip]))

    def get_retry_after(self, ip: str) -> float:
        """Seconds until oldest request in window expires."""
        now = time.time()
        cutoff = now - self._window
        with self._lock:
            if not self._hits[ip]:
                return 0.0
            oldest = self._hits[ip][0]
            if oldest > cutoff:
                return oldest - cutoff + 0.1  # small buffer
            return 0.0
