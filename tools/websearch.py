import time
import hashlib
from typing import Optional
from tools.base import BaseTool, ToolResult
import requests
from bs4 import BeautifulSoup


# ─── Cache ──────────────────────────────────────────────────────────

_cache: dict = {}
_CACHE_TTL = 300  # 5 minutes
_SEARCH_RESPONSE_MAX_BYTES = 750_000
_SEARCH_RESPONSE_CHUNK_BYTES = 64_000


def _read_search_response(response: requests.Response) -> str:
    """Read a search response incrementally under a fixed memory budget."""
    chunks: list[bytes] = []
    total = 0
    try:
        for chunk in response.iter_content(chunk_size=_SEARCH_RESPONSE_CHUNK_BYTES):
            if not chunk:
                continue
            remaining = _SEARCH_RESPONSE_MAX_BYTES - total
            if remaining <= 0:
                break
            chunks.append(chunk[:remaining])
            total += min(len(chunk), remaining)
            if len(chunk) > remaining:
                break
        return b"".join(chunks).decode("utf-8", errors="replace")
    finally:
        response.close()


def _cache_key(query: str, num_results: int, region: str, time_filter: str) -> str:
    raw = f"{query}|{num_results}|{region}|{time_filter}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _cache_get(key: str) -> Optional[list]:
    if key in _cache:
        entry = _cache[key]
        if time.time() - entry["ts"] < _CACHE_TTL:
            return entry["results"]
        del _cache[key]
    return None


def _cache_set(key: str, results: list):
    _cache[key] = {"results": results, "ts": time.time()}
    # Evict oldest if cache too big
    if len(_cache) > 100:
        oldest = min(_cache, key=lambda k: _cache[k]["ts"])
        del _cache[oldest]


# ─── Search Engines ─────────────────────────────────────────────────

_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

_TIME_MAP = {
    "day": "d",
    "week": "w",
    "month": "m",
    "year": "y",
}


def _search_ddg_lite(query: str, num_results: int, region: str, time_filter: str) -> dict:
    """Primary: DuckDuckGo Lite."""
    url = "https://lite.duckduckgo.com/lite/"
    data = {"q": query}
    if region:
        data["kl"] = region
    if time_filter and time_filter in _TIME_MAP:
        data["df"] = _TIME_MAP[time_filter]

    resp = requests.post(
        url,
        data=data,
        headers=_HEADERS,
        timeout=10,
        allow_redirects=False,
        stream=True,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(_read_search_response(resp), "html.parser")

    results = []
    for link in soup.find_all("a", class_="result-link"):
        # Snippet is in sibling/parent elements
        snippet = ""
        parent = link.find_parent("td", class_="result-snippet")
        if parent:
            snippet = parent.get_text(strip=True)
        results.append({
            "title": link.get_text(strip=True),
            "url": link.get("href", ""),
            "snippet": snippet,
        })
        if len(results) >= num_results:
            break

    # Did-you-mean suggestions
    suggestion = None
    sug_el = soup.find("a", class_="did-you-mean")
    if sug_el:
        suggestion = sug_el.get_text(strip=True)

    return {"results": results, "suggestion": suggestion}


def _search_ddg_html(query: str, num_results: int, region: str, time_filter: str) -> dict:
    """Fallback 1: DuckDuckGo HTML endpoint."""
    url = "https://html.duckduckgo.com/html/"
    data = {"q": query}
    if region:
        data["kl"] = region
    if time_filter and time_filter in _TIME_MAP:
        data["df"] = _TIME_MAP[time_filter]

    resp = requests.post(
        url,
        data=data,
        headers=_HEADERS,
        timeout=10,
        allow_redirects=False,
        stream=True,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(_read_search_response(resp), "html.parser")

    results = []
    for item in soup.find_all("div", class_="result"):
        title_el = item.find("a", class_="result__a")
        snippet_el = item.find("a", class_="result__snippet")
        url_el = item.find("a", class_="result__url")
        if title_el:
            results.append({
                "title": title_el.get_text(strip=True),
                "url": url_el.get_text(strip=True) if url_el else "",
                "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
            })
            if len(results) >= num_results:
                break

    suggestion = None
    sug_el = soup.find("a", class_="did-you-mean")
    if sug_el:
        suggestion = sug_el.get_text(strip=True)

    return {"results": results, "suggestion": suggestion}


def _search_browser(query: str, num_results: int, **kwargs) -> dict:
    """Fallback 2: Browser-based search via tools/browser.py."""
    try:
        from tools.browser import browser_search
    except ImportError:
        raise RuntimeError("browser.py not available")

    result = browser_search(query, engine="duckduckgo")
    if not result.get("success"):
        raise RuntimeError(result.get("error", "browser search failed"))

    # Navigate result page, extract links via browser text
    from tools.browser import _ensure_browser
    browser = _ensure_browser()
    text_result = browser.do("get_visible_text")
    if not text_result.get("success"):
        raise RuntimeError("could not get page text")

    # Simple text-based extraction (no DOM access from sync)
    lines = [l.strip() for l in text_result["text"].splitlines() if l.strip()]
    results = []
    i = 0
    while i < len(lines) and len(results) < num_results:
        line = lines[i]
        if line.startswith("http"):
            # Next line likely snippet
            snippet = lines[i + 1] if i + 1 < len(lines) else ""
            title = snippet.split(".")[0] if snippet else line
            results.append({"title": title, "url": line, "snippet": snippet})
            i += 2
        else:
            i += 1

    return {"results": results, "suggestion": None}


# ─── Retry Wrapper ──────────────────────────────────────────────────

def _with_retry(fn, *args, max_retries=2, base_delay=1.0, **kwargs):
    """Call fn with exponential backoff retry."""
    last_err = None
    for attempt in range(max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(base_delay * (2 ** attempt))
    raise last_err


# ─── Main Search ────────────────────────────────────────────────────

def search(
    query: str,
    num_results: int = 5,
    region: str = "",
    time_filter: str = "",
) -> dict:
    """
    Search web with multi-engine fallback.

    Args:
        query: Search query
        num_results: Number of results (default 5, max 20)
        region: Region code (optional, e.g. "us-en")
        time_filter: Time filter ("day", "week", "month", "year")

    Returns:
        dict with keys: results, suggestion, count, engine_used
    """
    num_results = min(max(num_results, 1), 20)
    key = _cache_key(query, num_results, region, time_filter)

    # Check cache
    cached = _cache_get(key)
    if cached is not None:
        return cached

    engines = [
        ("ddg_lite", _search_ddg_lite),
        ("ddg_html", _search_ddg_html),
        ("browser", _search_browser),
    ]

    last_error = None
    for engine_name, engine_fn in engines:
        try:
            if engine_name == "browser":
                result = _with_retry(engine_fn, query, num_results)
            else:
                result = _with_retry(engine_fn, query, num_results, region, time_filter)

            if result["results"]:
                output = {
                    "results": result["results"],
                    "suggestion": result.get("suggestion"),
                    "count": len(result["results"]),
                    "engine_used": engine_name,
                }
                _cache_set(key, output)
                return output
        except Exception as e:
            last_error = e
            continue

    return {
        "results": [],
        "suggestion": None,
        "count": 0,
        "engine_used": None,
        "error": f"All search engines failed. Last error: {last_error}",
    }


# ─── Tool Class ─────────────────────────────────────────────────────

class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Search the web via DuckDuckGo with multi-engine fallback"

    def run(self, query: str, num_results: int = 5, region: str = "", time_filter: str = "") -> ToolResult:
        try:
            result = search(query, num_results, region, time_filter)

            if result.get("error"):
                return ToolResult(success=False, output="", error=result["error"])

            if not result["results"]:
                return ToolResult(success=False, output="", error="No results found.")

            output_parts = []

            if result.get("suggestion"):
                output_parts.append(f"Did you mean: {result['suggestion']}")

            output_parts.append(f"Results ({result['count']} found via {result['engine_used']}):")

            for i, r in enumerate(result["results"], 1):
                parts = [f"{i}. {r['title']}", f"   URL: {r['url']}"]
                if r.get("snippet"):
                    parts.append(f"   {r['snippet']}")
                output_parts.append("\n".join(parts))

            return ToolResult(success=True, output="\n\n".join(output_parts))

        except Exception as e:
            return ToolResult(success=False, output="", error=f"Search failed: {e}")
