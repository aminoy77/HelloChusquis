"""Security regressions for persistent cron job storage."""

import os
from pathlib import Path
import tempfile
import unittest

from core.cron import CronService


class TestCronStoragePermissions(unittest.TestCase):
    @staticmethod
    def _mode(path: Path) -> int:
        return path.stat().st_mode & 0o777

    def test_cron_store_is_atomic_and_owner_only(self):
        with tempfile.TemporaryDirectory() as directory:
            store_dir = Path(directory) / "cron"
            store_path = store_dir / "cron.json"
            service = CronService(store_path=store_path)
            service.add(name="job", interval=60, action="noop")

            self.assertEqual(self._mode(store_dir), 0o700)
            self.assertEqual(self._mode(store_path), 0o600)
            self.assertFalse(store_path.with_suffix(".tmp").exists())

    def test_loading_repairs_insecure_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            store_dir = Path(directory) / "cron"
            store_dir.mkdir(mode=0o755)
            store_path = store_dir / "cron.json"
            store_path.write_text('{"version": 1, "jobs": []}', encoding="utf-8")
            os.chmod(store_path, 0o644)

            CronService(store_path=store_path)

            self.assertEqual(self._mode(store_dir), 0o700)
            self.assertEqual(self._mode(store_path), 0o600)


if __name__ == "__main__":
    unittest.main()
