import hashlib
import json
import pickle
import time
from pathlib import Path

# Create cache directory
CACHE_DIR = Path.home() / ".hellochusquis" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_cache_key(messages, tools=None):
    """Generate a cache key based on messages and tools"""
    cache_data = {
        "messages": messages,
        "tools": tools
    }
    cache_string = json.dumps(cache_data, sort_keys=True)
    return hashlib.md5(cache_string.encode()).hexdigest()

def get_cached_response(cache_key):
    """Retrieve cached response if it exists and is not expired"""
    cache_file = CACHE_DIR / f"{cache_key}.pkl"
    if cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                
            # Check if cache is still valid (5 minutes expiry)
            if time.time() - cached_data['timestamp'] < 300:  # 5 minutes
                return cached_data['response']
        except:
            pass
    return None

def cache_response(cache_key, response):
    """Cache the response with a timestamp"""
    cache_file = CACHE_DIR / f"{cache_key}.pkl"
    try:
        cached_data = {
            'response': response,
            'timestamp': time.time()
        }
        with open(cache_file, 'wb') as f:
            pickle.dump(cached_data, f)
    except:
        pass