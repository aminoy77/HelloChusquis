import json
import hashlib
import time
from pathlib import Path
from typing import Optional


class Cache:
    """Intelligent response cache for similar queries."""
    
    def __init__(self, cache_dir: str = None, ttl: int = 3600):
        self.cache_dir = Path(cache_dir or str(Path.home() / ".hellochusquis" / "cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl  # Time to live in seconds
    
    def _hash(self, text: str) -> str:
        """Create hash for query."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    def get(self, text: str) -> Optional[str]:
        """Get cached response if valid."""
        key = self._hash(text)
        cache_file = self.cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            data = json.loads(cache_file.read_text())
            timestamp = data.get("timestamp", 0)
            
            # Check if expired
            if time.time() - timestamp > self.ttl:
                cache_file.unlink()
                return None
            
            return data.get("response")
        except:
            return None
    
    def set(self, text: str, response: str) -> None:
        """Cache a response."""
        key = self._hash(text)
        cache_file = self.cache_dir / f"{key}.json"
        
        data = {
            "query": text[:100],  # Store truncated for debugging
            "response": response,
            "timestamp": time.time()
        }
        
        cache_file.write_text(json.dumps(data))
    
    def clear(self) -> int:
        """Clear all cache files."""
        count = 0
        for f in self.cache_dir.glob("*.json"):
            f.unlink()
            count += 1
        return count
    
    def size(self) -> int:
        """Get cache size in bytes."""
        total = 0
        for f in self.cache_dir.glob("*.json"):
            total += f.stat().st_size
        return total


# Global cache instance
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


if __name__ == "__main__":
    print(f"Cache: {get_cache_size()} bytes")