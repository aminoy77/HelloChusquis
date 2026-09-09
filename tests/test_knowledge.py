"""Knowledge base: repo MDknowledge + user-local overrides, deduped ingest."""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import core.db_memory as db_memory


def _kb_file(root, rel, bullets):
    p = Path(root) / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("# Topic\n\n" + "\n".join(f"- {b}" for b in bullets) + "\n",
                 encoding="utf-8")
    return p


class TestKnowledgeBase(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.mkdtemp()
        self._repo = str(Path(self._tmpdir) / "repo")
        self._user = str(Path(self._tmpdir) / "user")
        self._orig = db_memory.MEMORY_DB_PATH
        db_memory.MEMORY_DB_PATH = Path(self._tmpdir) / "kb.db"

    def tearDown(self):
        db_memory.MEMORY_DB_PATH = self._orig
        shutil.rmtree(self._tmpdir, ignore_errors=True)

    def _load(self):
        return db_memory.load_knowledge(repo_dir=self._repo, user_dir=self._user)

    def test_user_file_overrides_repo_file(self):
        _kb_file(self._repo, "programming/python/lists.md", ["repo-only-fact-xyz"])
        _kb_file(self._user, "programming/python/lists.md", ["user-only-fact-xyz"])
        self._load()
        block = db_memory.recall_context("fact xyz")
        self.assertIn("user-only-fact-xyz", block)
        self.assertNotIn("repo-only-fact-xyz", block)

    def test_reingest_is_idempotent(self):
        _kb_file(self._repo, "geography/rivers.md", ["the nile is long"])
        self._load()
        before = db_memory._get_store().get_entry_count()
        self._load()
        self.assertEqual(db_memory._get_store().get_entry_count(), before)

    def test_changed_file_reingests(self):
        p = _kb_file(self._repo, "history/rome.md", ["rome founded 753 bc"])
        self._load()
        p.write_text("# Rome\n\n- rome fell 476 ad\n", encoding="utf-8")
        self._load()
        block = db_memory.recall_context("rome")
        self.assertIn("476 ad", block)
        self.assertNotIn("753 bc", block)

    def test_missing_user_dir_still_loads_repo(self):
        _kb_file(self._repo, "programming/python/lists.md", ["append adds to list end"])
        n = db_memory.load_knowledge(repo_dir=self._repo, user_dir=str(Path(self._tmpdir) / "nouser"))
        self.assertGreater(n, 0)
        self.assertIn("append", db_memory.recall_context("append list"))

    def test_code_fences_not_ingested(self):
        p = Path(self._repo) / "programming/python/fences.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# Fences\n\n```python\nsecret-fence-token-xyz\n```\n\n- visible bullet ok\n",
                     encoding="utf-8")
        self._load()
        self.assertNotIn("secret-fence-token-xyz", db_memory.recall_context("fence token"))
        self.assertIn("visible bullet ok", db_memory.recall_context("visible bullet"))


if __name__ == "__main__":
    unittest.main()
