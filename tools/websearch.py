"""Web search: maintained multi-engine client plus keyless API fallbacks.

Engines that scrape search pages (DuckDuckGo, Google, ...) block datacenter
IPs intermittently, so a single engine is not enough. The primary path uses
the maintained ``ddgs`` client; when it is blocked, keyless public APIs
(Wikipedia, Stack Overflow, Hacker News) answer instead.
"""

import hashlib
import re
import time
from urllib.parse import quote

import requests

from tools.base import BaseTool, ToolResult

_CACHE_TTL = 300       # successful results
_NEGATIVE_TTL = 60     # failed searches, so one blocked query is not retried in a loop
_MAX_CACHE = 100
_DEADLINE_S = 12       # whole-search budget
# shortcut: general web search runs on scraper engines, which datacenter IPs
# get blocked from; upgrade to a keyed provider (Brave/Tavily/Exa) for reliability.
_BACKENDS = "google,yahoo,duckduckgo,startpage,brave,mojeek"
_TIME_MAP = {"day": "d", "week": "w", "month": "m", "year": "y"}

_cache: dict = {}


def _cache_key(query: str, num_results: int, region: str, time_filter: str) -> str:
    raw = f"{query}|{num_results}|{region}|{time_filter}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str):
    entry = _cache.get(key)
    if entry and time.time() - entry["ts"] < entry["ttl"]:
        return entry["value"]
    _cache.pop(key, None)
    return None


def _cache_set(key: str, value, ttl: int = _CACHE_TTL) -> None:
    _cache[key] = {"value": value, "ts": time.time(), "ttl": ttl}
    while len(_cache) > _MAX_CACHE:
        oldest = min(_cache, key=lambda k: _cache[k]["ts"])
        del _cache[oldest]


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


# ─── Engines ──────────────────────────────────────────────────────────────

def _search_ddgs(query: str, num_results: int, region: str, time_filter: str) -> list[dict]:
    """General web search through the maintained ddgs client."""
    from ddgs import DDGS

    kwargs = {"max_results": num_results, "backend": _BACKENDS}
    if region:
        kwargs["region"] = region
    timelimit = _TIME_MAP.get(time_filter)
    if timelimit:
        kwargs["timelimit"] = timelimit

    last_error = None
    for attempt in range(2):
        try:
            with DDGS(timeout=5) as client:
                rows = client.text(query, **kwargs)
            return [
                {
                    "title": row.get("title") or "",
                    "url": row.get("href") or "",
                    "snippet": _strip_html(row.get("body") or ""),
                }
                for row in rows
                if row.get("href")
            ]
        except Exception as exc:  # scraping engines block and recover on retry
            last_error = exc
            if attempt == 0:
                time.sleep(1)
    raise last_error


def _search_wikipedia(query: str, num_results: int, region: str, time_filter: str) -> list[dict]:
    # shortcut: fallback engines ignore region/time_filter; upgrade: map params per engine.
    resp = requests.get(
        "https://en.wikipedia.org/w/api.php",
        params={"action": "query", "list": "search", "srsearch": query,
                "format": "json", "srlimit": num_results},
        timeout=5,
    )
    resp.raise_for_status()
    hits = resp.json().get("query", {}).get("search", [])
    return [
        {
            "title": hit.get("title", ""),
            "url": "https://en.wikipedia.org/wiki/" + quote(hit.get("title", "").replace(" ", "_")),
            "snippet": _strip_html(hit.get("snippet", "")),
        }
        for hit in hits
    ]


def _search_hackernews(query: str, num_results: int, region: str, time_filter: str) -> list[dict]:
    resp = requests.get(
        "https://hn.algolia.com/api/v1/search",
        params={"query": query, "hitsPerPage": num_results},
        timeout=5,
    )
    resp.raise_for_status()
    results = []
    for hit in resp.json().get("hits", []):
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        results.append({
            "title": hit.get("title") or hit.get("story_title") or "",
            "url": url,
            "snippet": _strip_html(hit.get("story_text") or hit.get("comment_text") or "")[:300],
        })
    return results


def _search_stackoverflow(query: str, num_results: int, region: str, time_filter: str) -> list[dict]:
    resp = requests.get(
        "https://api.stackexchange.com/2.3/search/advanced",
        params={"q": query, "site": "stackoverflow", "pagesize": num_results, "filter": "withbody"},
        timeout=5,
    )
    resp.raise_for_status()
    return [
        {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": _strip_html(item.get("body", ""))[:300],
        }
        for item in resp.json().get("items", [])
    ]



# ─── Main Search ──────────────────────────────────────────────────────────
def search(
    query: str,
    num_results: int = 5,
    region: str = "",
    time_filter: str = "",
) -> dict:
    """Search the web. Returns results, count, engine_used and (on failure) error."""
    if not str(query or "").strip():
        return {"results": [], "count": 0, "engine_used": None, "error": "Search query is required."}

    num_results = int(min(max(int(num_results), 1), 20))
    key = _cache_key(query, num_results, region, time_filter)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    started = time.monotonic()
    errors: list[str] = []
    used: list[str] = []
    found: list[dict] = []

    for name, engine in (
        ("web", _search_ddgs),
        ("wikipedia", _search_wikipedia),
        ("stackoverflow", _search_stackoverflow),
        ("hackernews", _search_hackernews),
    ):
        if time.monotonic() - started > _DEADLINE_S:
            errors.append(f"{name}: skipped (search deadline reached)")
            break
        try:
            results = engine(query, num_results, region, time_filter)
        except Exception as exc:
            errors.append(f"{name}: {type(exc).__name__}: {exc}")
            continue
        used.append(name)
        found.extend(results)
        # First engine with hits wins; the API engines exist for when the
        # scraping engines are blocked, not to mix sources into every answer.
        break

    if not used:
        payload = {
            "results": [],
            "count": 0,
            "engine_used": None,
            "error": "All search engines failed: " + "; ".join(errors),
        }
        _cache_set(key, payload, _NEGATIVE_TTL)
        return payload

    seen: set[str] = set()
    unique = []
    for item in found:
        if item["url"] and item["url"] not in seen:
            seen.add(item["url"])
            unique.append(item)

    payload = {
        "results": unique[:num_results],
        "count": min(len(unique), num_results),
        "engine_used": ",".join(used),
        "errors": errors,
    }
    _cache_set(key, payload)
    return payload


# ─── Tool Class ───────────────────────────────────────────────────────────

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web (multi-engine, with Wikipedia/Hacker News/Stack Overflow fallback)"

    def run(self, query: str, num_results: int = 5, region: str = "", time_filter: str = "") -> ToolResult:
        try:
            result = search(query, num_results, region, time_filter)
        except Exception as exc:
            return ToolResult(success=False, output="", error=f"Search failed: {exc}")

        if result.get("error"):
            return ToolResult(success=False, output="", error=result["error"])

        results = result["results"]
        if not results:
            return ToolResult(
                success=True,
                output=f"No results found for '{query}'. Try different or broader keywords.",
                data=[],
            )

        lines = [f"Results ({result['count']} via {result['engine_used']}):"]
        for index, item in enumerate(results, 1):
            lines.append(f"{index}. {item['title']}\n   URL: {item['url']}")
            if item.get("snippet"):
                lines.append(f"   {item['snippet']}")

        return ToolResult(success=True, output="\n\n".join(lines), data=results)
