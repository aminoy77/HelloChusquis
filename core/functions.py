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
    import ast
    allowed = set("0123456789.+-*/() ")
    if any(c not in allowed for c in expression):
        return {"error": "Invalid characters in expression"}
    try:
        result = ast.literal_eval(expression)
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
        except Exception:
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
    """Open a URL in the browser and keep it open."""
    from tools.browser import browser_open as _browser_open
    return _browser_open(url)


def browser_click(selector: str = None, text: str = None, xpath: str = None, index: int = 0) -> dict:
    """Click an element on the page by selector or text."""
    from tools.browser import browser_click as _browser_click
    return _browser_click(selector, text, xpath, index)


def browser_double_click(selector: str = None, text: str = None, xpath: str = None) -> dict:
    """Double-click an element."""
    from tools.browser import browser_double_click as _browser_double_click
    return _browser_double_click(selector, text, xpath)


def browser_right_click(selector: str = None, text: str = None, xpath: str = None) -> dict:
    """Right-click an element."""
    from tools.browser import browser_right_click as _browser_right_click
    return _browser_right_click(selector, text, xpath)


def browser_type(text: str, selector: str = None, clear_first: bool = True) -> dict:
    """Type text into an input field."""
    from tools.browser import browser_type as _browser_type
    return _browser_type(text, selector, clear_first)


def browser_scroll(direction: str = 'down', amount: int = 3) -> dict:
    """Scroll the page up or down."""
    from tools.browser import browser_scroll as _browser_scroll
    return _browser_scroll(direction, amount)


def browser_screenshot(path: str = None, full_page: bool = False) -> dict:
    """Take a screenshot of the current page."""
    from tools.browser import browser_screenshot as _browser_screenshot
    return _browser_screenshot(path, full_page)


def browser_get_text(selector: str = None) -> dict:
    """Get text content from the page or an element."""
    from tools.browser import browser_get_text as _browser_get_text
    return _browser_get_text(selector)


def browser_get_visible_text() -> dict:
    """Get visible text from the page."""
    from tools.browser import browser_get_visible_text as _browser_get_visible_text
    return _browser_get_visible_text()


def browser_search(query: str, engine: str = 'google') -> dict:
    """Search the web using a search engine."""
    from tools.browser import browser_search as _browser_search
    return _browser_search(query, engine)


def browser_find(pattern: str) -> dict:
    """Find elements on the page matching a pattern."""
    from tools.browser import browser_find as _browser_find
    return _browser_find(pattern)


def browser_fill_form(form_data: dict) -> dict:
    """Fill a form with field-value pairs."""
    from tools.browser import browser_fill_form as _browser_fill_form
    return _browser_fill_form(form_data)


def browser_submit_form(selector: str = 'form') -> dict:
    """Submit a form."""
    from tools.browser import browser_submit_form as _browser_submit_form
    return _browser_submit_form(selector)


def browser_hover(selector: str = None, text: str = None, xpath: str = None) -> dict:
    """Hover over an element."""
    from tools.browser import browser_hover as _browser_hover
    return _browser_hover(selector, text, xpath)


def browser_wait_for_element(selector: str, timeout: int = 30) -> dict:
    """Wait for an element to appear."""
    from tools.browser import browser_wait_for_element as _browser_wait
    return _browser_wait(selector, timeout)


def browser_wait_for_navigation(timeout: int = 30) -> dict:
    """Wait for page navigation."""
    from tools.browser import browser_wait_for_navigation as _browser_wait_nav
    return _browser_wait_nav(timeout)


def browser_execute_script(script: str) -> dict:
    """Execute JavaScript on the page."""
    from tools.browser import browser_execute_script as _browser_script
    return _browser_script(script)


def browser_get_url() -> dict:
    """Get current page URL."""
    from tools.browser import browser_get_url as _browser_get_url
    return _browser_get_url()


def browser_get_title() -> dict:
    """Get current page title."""
    from tools.browser import browser_get_title as _browser_get_title
    return _browser_get_title()


def browser_get_cookies() -> dict:
    """Get all cookies from the browser context."""
    from tools.browser import browser_get_cookies as _browser_cookies
    return _browser_cookies()


def browser_go_back() -> dict:
    """Go back in browser history."""
    from tools.browser import browser_go_back as _browser_back
    return _browser_back()


def browser_go_forward() -> dict:
    """Go forward in browser history."""
    from tools.browser import browser_go_forward as _browser_forward
    return _browser_forward()


def browser_reload() -> dict:
    """Reload the current page."""
    from tools.browser import browser_reload as _browser_reload
    return _browser_reload()


def browser_press_key(key: str) -> dict:
    """Press a keyboard key (Enter, Tab, Escape, etc)."""
    from tools.browser import browser_press_key as _browser_key
    return _browser_key(key)


def browser_scroll_to_element(selector: str) -> dict:
    """Scroll to a specific element."""
    from tools.browser import browser_scroll_to_element as _browser_scroll_to
    return _browser_scroll_to(selector)


def browser_open_new_tab(url: str = None) -> dict:
    """Open a new browser tab."""
    from tools.browser import browser_open_new_tab as _browser_new_tab
    return _browser_new_tab(url)


def browser_switch_to_page(index: int = 0) -> dict:
    """Switch to a specific tab by index."""
    from tools.browser import browser_switch_to_page as _browser_switch
    return _browser_switch(index)


def browser_health() -> dict:
    """Check if browser is healthy and responsive."""
    from tools.browser import browser_health as _browser_health
    return _browser_health()


def browser_close() -> dict:
    """Close the browser."""
    from tools.browser import browser_close as _browser_close
    return _browser_close()


def browser_explore(start_url: str, task: str) -> dict:
    """Explore a website and gather information based on a task."""
    result = browser_open(start_url)
    if not result.get('success'):
        return result

    find_result = browser_find(task)
    text_result = browser_get_text()

    return {
        'success': True,
        'url': result.get('url'),
        'title': result.get('title'),
        'found_count': find_result.get('count', 0),
        'elements': find_result.get('elements', []),
        'text': text_result.get('text', '')[:2000]
    }