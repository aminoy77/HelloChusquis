"""Deprecated compatibility cache with safe on-disk persistence."""

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Optional


class Cache:
    """Intelligent response cache for similar queries."""

    def __init__(self, cache_dir: str | None = None, ttl: int = 3600):
        self.cache_dir = Path(cache_dir or str(Path.home() / ".hellochusquis" / "cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.cache_dir, 0o700)
        self.ttl = ttl

    def _hash(self, text: str) -> str:
        """Create a stable cache key for a query."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    def get(self, text: str) -> Optional[str]:
        """Get a cached response when its TTL has not expired."""
        cache_file = self.cache_dir / f"{self._hash(text)}.json"
        if not cache_file.exists():
            return None
        try:
            data = json.loads(cache_file.read_text(encoding="utf-8"))
            if time.time() - data.get("timestamp", 0) > self.ttl:
                cache_file.unlink(missing_ok=True)
                return None
            return data.get("response")
        except (json.JSONDecodeError, OSError, TypeError):
            return None

    def set(self, text: str, response: str) -> None:
        """Persist a cache entry atomically with owner-only permissions."""
        cache_file = self.cache_dir / f"{self._hash(text)}.json"
        data = {"query": text[:100], "response": response, "timestamp": time.time()}
        fd, temporary_path = tempfile.mkstemp(prefix=f".{cache_file.name}.", dir=self.cache_dir)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as temporary_file:
                json.dump(data, temporary_file)
                temporary_file.flush()
                os.fsync(temporary_file.fileno())
            os.replace(temporary_path, cache_file)
        finally:
            if os.path.exists(temporary_path):
                os.unlink(temporary_path)

    def clear(self) -> int:
        """Clear all cache files owned by this cache directory."""
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except OSError:
                continue
        return count

    def size(self) -> int:
        """Get cache size in bytes while tolerating concurrent cleanup."""
        total = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                total += cache_file.stat().st_size
            except OSError:
                continue
        return total


_cache = Cache()


def get_cached_response(query: str) -> Optional[str]:
    """Check cache for query."""
    return _cache.get(query)


def cache_response(query: str, response: str) -> None:
    """Cache a response."""
    _cache.set(query, response)


def clear_cache() -> int:
    """Clear all cached responses."""
    return _cache.clear()


def get_cache_size() -> int:
    """Get cache size in bytes."""
    return _cache.size()
