"""Web search engine fallback and result semantics."""

import unittest
from unittest.mock import patch

from tools import websearch


def _hit(title, url, snippet=""):
    return {"title": title, "url": url, "snippet": snippet}


class TestWebSearchEngines(unittest.TestCase):
    def setUp(self):
        websearch._cache.clear()

    def test_falls_back_to_keyless_apis_when_scraping_engine_is_blocked(self):
        with patch.object(websearch, "_search_ddgs", side_effect=RuntimeError("blocked")), patch.object(
            websearch, "_search_wikipedia", return_value=[_hit("Async", "https://en.wikipedia.org/wiki/Async")]
        ):
            result = websearch.search("asyncio", num_results=3)

        self.assertEqual(result["engine_used"], "wikipedia")
        self.assertEqual(result["results"][0]["url"], "https://en.wikipedia.org/wiki/Async")
        self.assertIn("blocked", result["errors"][0])

    def test_all_engines_failing_returns_error(self):
        with patch.object(websearch, "_search_ddgs", side_effect=RuntimeError("blocked")), patch.object(
            websearch, "_search_wikipedia", side_effect=RuntimeError("down")
        ), patch.object(websearch, "_search_hackernews", side_effect=RuntimeError("down")), patch.object(
            websearch, "_search_stackoverflow", side_effect=RuntimeError("down")
        ):
            result = websearch.search("asyncio", num_results=3)

        self.assertEqual(result["results"], [])
        self.assertIn("All search engines failed", result["error"])

    def test_empty_results_are_a_successful_search(self):
        tool = websearch.WebSearchTool()
        with patch.object(websearch, "_search_ddgs", return_value=[]), patch.object(
            websearch, "_search_wikipedia", return_value=[]
        ), patch.object(websearch, "_search_hackernews", return_value=[]), patch.object(
            websearch, "_search_stackoverflow", return_value=[]
        ):
            result = tool.run("zzzz-no-such-thing")

        self.assertTrue(result.success)
        self.assertIn("No results found", result.output)

    def test_failed_search_is_cached_as_negative(self):
        with patch.object(websearch, "_search_ddgs", side_effect=RuntimeError("blocked")) as ddg, patch.object(
            websearch, "_search_wikipedia", side_effect=RuntimeError("down")
        ), patch.object(websearch, "_search_hackernews", side_effect=RuntimeError("down")), patch.object(
            websearch, "_search_stackoverflow", side_effect=RuntimeError("down")
        ):
            first = websearch.search("asyncio", num_results=3)
            second = websearch.search("asyncio", num_results=3)

        self.assertEqual(first["error"], second["error"])
        self.assertEqual(ddg.call_count, 1)

    def test_duplicate_urls_are_dropped_and_results_capped(self):
        with patch.object(websearch, "_search_ddgs", return_value=[
            _hit("A", "https://example.com/a"),
            _hit("A again", "https://example.com/a"),
            _hit("B", "https://example.com/b"),
        ]):
            result = websearch.search("dup", num_results=2)

        self.assertEqual([r["url"] for r in result["results"]], ["https://example.com/a", "https://example.com/b"])
        self.assertEqual(result["count"], 2)

    def test_float_num_results_from_the_model_is_accepted(self):
        with patch.object(websearch, "_search_ddgs", return_value=[_hit("A", "https://example.com/a")]):
            result = websearch.search("floats", num_results=5.0)

        self.assertEqual(result["count"], 1)


if __name__ == "__main__":
    unittest.main()
