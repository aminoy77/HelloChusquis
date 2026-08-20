"""Regression tests for owner-only SQLite storage containing agent data."""

from pathlib import Path
import sqlite3
import stat
import tempfile
import unittest
from unittest.mock import patch

from core import db_memory, session


class TestSqliteStoragePermissions(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary_directory.name)
        self.session_home_patch = patch.object(session.Path, "home", return_value=self.home)
        self.memory_home_patch = patch.object(db_memory.Path, "home", return_value=self.home)
        self.session_home_patch.start()
        self.memory_home_patch.start()

    def tearDown(self):
        self.memory_home_patch.stop()
        self.session_home_patch.stop()
        self.temporary_directory.cleanup()

    def _managed_path(self, name):
        directory = self.home / ".hellochusquis"
        directory.mkdir()
        directory.chmod(0o755)
        path = directory / name
        sqlite3.connect(path).close()
        path.chmod(0o644)
        return directory, path

    def test_session_database_permissions_are_repaired(self):
        directory, path = self._managed_path("sessions.db")
        manager = session.SessionManager(path)
        manager.close()

        self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_memory_database_permissions_are_repaired(self):
        directory, path = self._managed_path("memory.db")
        connection = db_memory._connect(path)
        connection.close()

        self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)

    def test_explicit_in_memory_databases_do_not_require_a_file(self):
        session_manager = session.SessionManager(":memory:")
        session_manager.create_session("agent", "model")
        session_manager.close()

        connection = db_memory._connect(":memory:")
        connection.execute("CREATE TABLE example (id INTEGER PRIMARY KEY)")
        connection.close()

        self.assertFalse((Path.cwd() / ":memory:").exists())


if __name__ == "__main__":
    unittest.main()
