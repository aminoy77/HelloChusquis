"""Regression tests for bounded dynamic memory queries."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from core.db_memory import MemoryStore


class TestMemoryQueryBounds(unittest.TestCase):
    def test_keyword_search_bounds_token_expansion_in_sql_statement(self):
        with tempfile.TemporaryDirectory() as directory:
            store = MemoryStore(Path(directory) / "memory.sqlite")
            traced: list[str] = []
            store.conn.set_trace_callback(traced.append)
            try:
                with patch("core.db_memory.re.findall", return_value=["token"] * 1_000):
                    store.search_entries_keyword("ignored", limit=10_000)
            finally:
                store.close()

        select_statements = [statement for statement in traced if "FROM memory_entries" in statement]
        self.assertEqual(len(select_statements), 1)
        self.assertLess(len(select_statements[0]), 2_000)


if __name__ == "__main__":
    unittest.main()
