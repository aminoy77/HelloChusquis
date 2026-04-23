from __future__ import annotations
import hashlib
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    key: str
    value: Any
    created_at: float
    expires_at: float | None = None
    hit_count: int = 0

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class SmartCache:
    """Intelligent caching with TTL and LRU eviction."""

    def __init__(self, max_size: int = 1000, default_ttl: int = 3600):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def _make_key(self, *args, **kwargs) -> str:
        data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(data.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        entry = self._cache.get(key)
        if entry and not entry.is_expired():
            entry.hit_count += 1
            self._hits += 1
            return entry.value
        elif entry:
            del self._cache[key]
        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl: int | None = None):
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        expires_at = time.time() + (ttl or self.default_ttl) if ttl else None
        self._cache[key] = CacheEntry(
            key=key,
            value=value,
            created_at=time.time(),
            expires_at=expires_at
        )

    def remember(self, key: str, value: Any, ttl: int | None = None):
        """Decorator-style caching."""
        self.set(key, value, ttl)
        return value

    def memoize(self, ttl: int | None = None):
        """Decorator for memoizing function results."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                key = self._make_key(func.__name__, *args, **kwargs)
                cached = self.get(key)
                if cached is not None:
                    return cached
                result = func(*args, **kwargs)
                self.set(key, result, ttl)
                return result
            return wrapper
        return decorator

    def invalidate(self, key: str):
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def _evict_lru(self):
        if not self._cache:
            return
        lru_key = min(self._cache.keys(), key=lambda k: self._cache[k].created_at)
        del self._cache[lru_key]

    def stats(self) -> dict:
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.1f}%"
        }

    def cleanup(self):
        """Remove expired entries."""
        expired = [k for k, v in self._cache.items() if v.is_expired()]
        for k in expired:
            del self._cache[k]
        return len(expired)


# Global cache instance
_global_cache = None


def get_cache() -> SmartCache:
    global _global_cache
    if _global_cache is None:
        _global_cache = SmartCache()
    return _global_cache