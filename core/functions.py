"""Built-in functions for HelloChusquis."""

from __future__ import annotations
import json
import os
import re
import subprocess
import hashlib
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


def get_current_time() -> str:
    """Get current time in various formats."""
    now = datetime.now()
    return {
        "iso": now.isoformat(),
        "timestamp": now.timestamp(),
        "formatted": now.strftime("%Y-%m-%d %H:%M:%S"),
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "unix": int(now.timestamp())
    }


def calculate(expression: str) -> float:
    """Safe mathematical expression evaluator."""
    allowed = set("0123456789.+-*/() ")
    if any(c not in allowed for c in expression):
        return {"error": "Invalid characters in expression"}
    try:
        result = eval(expression)
        return {"result": result, "expression": expression}
    except Exception as e:
        return {"error": str(e)}


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """Hash a string with various algorithms."""
    algorithms = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
        "blake2b": hashlib.blake2b,
        "blake2s": hashlib.blake2s
    }
    if algorithm not in algorithms:
        return {"error": f"Unknown algorithm: {algorithm}"}
    h = algorithms[algorithm](text.encode())
    return {"hash": h.hexdigest(), "algorithm": algorithm, "length": len(h.hexdigest())}


def base64_encode(text: str, encode: bool = True) -> str:
    """Encode or decode base64."""
    if encode:
        return {"result": base64.b64encode(text.encode()).decode(), "mode": "encode"}
    else:
        try:
            return {"result": base64.b64decode(text.encode()).decode(), "mode": "decode"}
        except:
            return {"error": "Invalid base64 string"}


def url_encode(text: str, encode: bool = True) -> str:
    """URL encode or decode."""
    from urllib.parse import quote, unquote
    if encode:
        return {"result": quote(text), "mode": "encode"}
    else:
        return {"result": unquote(text), "mode": "decode"}


def file_exists(path: str) -> bool:
    """Check if file exists."""
    return {"exists": Path(path).exists(), "path": path}


def file_size(path: str) -> dict:
    """Get file size."""
    p = Path(path)
    if not p.exists():
        return {"error": "File not found"}
    return {"size": p.stat().st_size, "path": path, "human": format_size(p.stat().st_size)}


def list_directory(path: str, pattern: str = "*") -> dict:
    """List directory contents."""
    p = Path(path)
    if not p.exists():
        return {"error": "Directory not found"}
    if not p.is_dir():
        return {"error": "Not a directory"}
    files = [f.name for f in p.glob(pattern)]
    return {"files": files, "count": len(files), "path": path}


def read_json(path: str) -> dict:
    """Read JSON file."""
    try:
        with open(path) as f:
            return {"data": json.load(f)}
    except Exception as e:
        return {"error": str(e)}


def write_json(path: str, data: dict, indent: int = 2) -> dict:
    """Write JSON file."""
    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=indent)
        return {"saved": True, "path": path}
    except Exception as e:
        return {"error": str(e)}


def get_environment() -> dict:
    """Get environment variables."""
    return dict(os.environ)


def get_system_info() -> dict:
    """Get system information."""
    import platform
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version()
    }


def get_ip_address() -> dict:
    """Get public IP address."""
    import httpx
    try:
        r = httpx.get("https://api.ipify.org?format=json", timeout=5)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def check_website(url: str) -> dict:
    """Check if website is accessible."""
    import httpx
    try:
        r = httpx.get(url, timeout=10, follow_redirects=True)
        return {
            "url": url,
            "status": r.status_code,
            "ok": r.status_code < 400,
            "headers": dict(r.headers)
        }
    except Exception as e:
        return {"error": str(e)}


def get_timestamp(days: int = 0) -> dict:
    """Get timestamp with offset."""
    dt = datetime.now() + timedelta(days=days)
    return {
        "timestamp": dt.timestamp(),
        "iso": dt.isoformat(),
        "days_offset": days
    }


def text_stats(text: str) -> dict:
    """Get text statistics."""
    return {
        "length": len(text),
        "words": len(text.split()),
        "lines": len(text.split("\n")),
        "chars": len(text.replace(" ", "")),
        "uppercase": sum(1 for c in text if c.isupper()),
        "lowercase": sum(1 for c in text if c.islower()),
        "digits": sum(1 for c in text if c.isdigit())
    }


def format_size(size: int) -> str:
    """Format file size to human readable."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def generate_uuid() -> str:
    """Generate a UUID."""
    import uuid
    return {"uuid": str(uuid.uuid4()), "version": 4}


def generate_random_string(length: int = 32, charset: str = "alphanumeric") -> str:
    """Generate random string."""
    import secrets
    charsets = {
        "alphanumeric": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        "alpha": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "numeric": "0123456789",
        "hex": "0123456789abcdef",
        "ascii": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    }
    chars = charsets.get(charset, charsets["alphanumeric"])
    return {"string": "".join(secrets.choice(chars) for _ in range(length)), "length": length}


def validate_email(email: str) -> bool:
    """Validate email address."""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return {"valid": bool(re.match(pattern, email)), "email": email}


def validate_url(url: str) -> bool:
    """Validate URL."""
    pattern = r"^https?://[^\s]+$"
    return {"valid": bool(re.match(pattern, url)), "url": url}


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    slug = text.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return {"slug": slug, "original": text}


def truncate(text: str, length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= length:
        return {"text": text, "truncated": False}
    return {"text": text[:length - len(suffix)] + suffix, "truncated": True}


def word_count(text: str) -> dict:
    """Count words in text."""
    words = text.split()
    return {
        "words": len(words),
        "unique": len(set(words)),
        "avg_length": sum(len(w) for w in words) / len(words) if words else 0
    }


def extract_links(text: str) -> dict:
    """Extract URLs from text."""
    pattern = r"https?://[^\s]+"
    links = re.findall(pattern, text)
    return {"links": links, "count": len(links)}


def extract_emails(text: str) -> dict:
    """Extract emails from text."""
    pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    emails = re.findall(pattern, text)
    return {"emails": emails, "count": len(emails)}


# Browser automation functions
def browser_open(url: str) -> dict:
    """Open a URL in the browser and start automation."""
    from tools.browser import get_browser_tools
    tools = get_browser_tools()
    return tools.browser_navigate(url)


def browser_click(selector: str = None, text: str = None) -> dict:
    """Click an element on the page by selector or text."""
    from tools.browser import get_browser_tools
    tools = get_browser_tools()
    return tools.browser_click(selector, text)


def browser_type(text: str, selector: str = None) -> dict:
    """Type text into an input field."""
    from tools.browser import get_browser_tools
    tools = get_browser_tools()
    return tools.browser_type(text, selector)


def browser_scroll(direction: str = 'down', amount: int = 3) -> dict:
    """Scroll the page up or down."""
    from tools.browser import get_browser_tools
    tools = get_browser_tools()
    return tools.browser_scroll(direction, amount)


def browser_screenshot(path: str = None, full_page: bool = False) -> dict:
    """Take a screenshot of the current page."""
    from tools.browser import get_browser_tools
    tools = get_browser_tools()
    return tools.browser_screenshot(path, full_page)


def browser_get_text(selector: str = None) -> dict:
    """Get text content from the page or an element."""
    from tools.browser import get_browser_tools
    tools = get_browser_tools()
    return tools.browser_get_text(selector)


def browser_search(query: str, engine: str = 'google') -> dict:
    """Search the web using a search engine."""
    from tools.browser import get_browser_tools
    tools = get_browser_tools()
    return tools.browser_search(query, engine)


def browser_find(pattern: str) -> dict:
    """Find elements on the page matching a pattern."""
    from tools.browser import get_browser_tools
    tools = get_browser_tools()
    return tools.browser_find(pattern)


def browser_fill_form(form_data: dict) -> dict:
    """Fill a form with field-value pairs."""
    from tools.browser import get_browser_tools
    tools = get_browser_tools()
    return tools.browser_fill_form(form_data)


def browser_close() -> dict:
    """Close the browser."""
    from tools.browser import get_browser_tools
    tools = get_browser_tools()
    return tools.browser_close()


def browser_explore(start_url: str, task: str) -> dict:
    """Explore a website and gather information based on a task."""
    from tools.browser import get_browser_tools
    tools = get_browser_tools()
    return tools.browser_explore(start_url, task)