# DEPRECATED: This module is not used. Consider removing.
"""Utility functions for HelloChusquis."""

import re
import json
import base64
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path


def uuid() -> str:
    """Generate UUID."""
    import uuid
    return {"uuid": str(uuid.uuid4()), "version": 4}


def random_string(length: int = 32, charset: str = "alphanumeric") -> str:
    """Generate random string."""
    charsets = {
        "alphanumeric": string.ascii_letters + string.digits,
        "alpha": string.ascii_letters,
        "numeric": string.digits,
        "hex": string.hexdigits.lower(),
    }
    chars = charsets.get(charset, charsets["alphanumeric"])
    return {"string": "".join(secrets.choice(chars) for _ in range(length)), "length": length}


def random_int(min_val: int = 0, max_val: int = 100) -> int:
    """Generate random integer."""
    return {"int": secrets.randbelow(max_val - min_val + 1) + min_val, "min": min_val, "max": max_val}


def random_choice(options: list) -> any:
    """Random choice from list."""
    return {"choice": secrets.choice(options), "options": options}


def timestamp() -> float:
    """Get current timestamp."""
    return {"timestamp": datetime.now().timestamp(), "iso": datetime.now().isoformat()}


def format_timestamp(timestamp: float, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format timestamp."""
    return {"formatted": datetime.fromtimestamp(timestamp).strftime(fmt)}


def parse_date(date_str: str, fmt: str = "%Y-%m-%d") -> str:
    """Parse date string."""
    return {"parsed": datetime.strptime(date_str, fmt).isoformat(), "input": date_str}


def date_add(date_str: str, days: int = 0, hours: int = 0) -> str:
    """Add time to date."""
    dt = datetime.fromisoformat(date_str)
    delta = timedelta(days=days, hours=hours)
    return {"result": (dt + delta).isoformat()}


def date_diff(date1: str, date2: str) -> str:
    """Calculate date difference."""
    d1 = datetime.fromisoformat(date1)
    d2 = datetime.fromisoformat(date2)
    diff = d2 - d1
    return {"days": diff.days, "seconds": diff.seconds, "hours": diff.total_seconds() / 3600}


def url_parse(url: str) -> dict:
    """Parse URL."""
    from urllib.parse import urlparse, parse_qs
    p = urlparse(url)
    return {
        "scheme": p.scheme, "netloc": p.netloc, "path": p.path,
        "params": p.params, "query": parse_qs(p.query), "fragment": p.fragment
    }


def url_build(scheme: str = "https", netloc: str = "", path: str = "", query: dict = None) -> str:
    """Build URL."""
    from urllib.parse import urlencode, urlunsplit
    return {"url": urlunsplit((scheme, netloc, path, urlencode(query or {}), ""))}


def slug(text: str) -> str:
    """Create URL slug."""
    slug = text.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return {"slug": slug.strip("-"), "original": text}


def truncate(text: str, length: int = 100, suffix: str = "...") -> str:
    """Truncate text."""
    if len(text) <= length:
        return {"text": text, "truncated": False}
    return {"text": text[:length - len(suffix)] + suffix, "truncated": True}


def escape_html(text: str) -> str:
    """Escape HTML."""
    return {"escaped": text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")}


def unescape_html(text: str) -> str:
    """Unescape HTML."""
    return {"unescaped": text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")}


def escape_json(text: str) -> str:
    """Escape for JSON."""
    return {"escaped": json.dumps(text)}


def unescape_json(text: str) -> str:
    """Unescape from JSON."""
    return {"unescaped": json.loads(text)}


def bytes_to_size(size: int) -> str:
    """Convert bytes to human readable."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return {"size": f"{size:.2f} {unit}"}
        size /= 1024
    return {"size": f"{size:.2f} PB"}


def size_to_bytes(size_str: str) -> int:
    """Convert size string to bytes."""
    units = {"B": 1, "KB": 1024, "MB": 1024**2, "GB": 1024**3, "TB": 1024**4}
    for unit, mult in units.items():
        if size_str.endswith(unit):
            return {"bytes": int(size_str[:-len(unit)]) * mult}
    return {"bytes": int(size_str)}


def pluralize(word: str, count: int) -> str:
    """Pluralize word."""
    if count == 1:
        return {"word": word}
    if word.endswith("y") and word[-2] not in "aeiou":
        return {"word": word[:-1] + "ies"}
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return {"word": word + "es"}
    return {"word": word + "s"}


def capitalize_words(text: str) -> str:
    """Capitalize each word."""
    return {"capitalized": " ".join(w.capitalize() for w in text.split())}


def reverse_text(text: str) -> str:
    """Reverse text."""
    return {"reversed": text[::-1]}


def palindrome(text: str) -> bool:
    """Check if palindrome."""
    cleaned = re.sub(r"[\s]", "", text.lower())
    return {"is_palindrome": cleaned == cleaned[::-1], "text": text}


def word_reverse(text: str) -> str:
    """Reverse word order."""
    return {"reversed": " ".join(text.split()[::-1])}


def extract_numbers(text: str) -> list:
    """Extract numbers from text."""
    nums = re.findall(r"-?\d+\.?\d*", text)
    return {"numbers": [float(n) if "." in n else int(n) for n in nums], "count": len(nums)}


def extract_hashtags(text: str) -> list:
    """Extract hashtags."""
    tags = re.findall(r"#\w+", text)
    return {"hashtags": tags, "count": len(tags)}


def extract_mentions(text: str) -> list:
    """Extract mentions."""
    mentions = re.findall(r"@\w+", text)
    return {"mentions": mentions, "count": len(mentions)}