"""Fase 1: telegram sin token/allow falla limpio, sin traceback."""
import os
import site
import subprocess
import sys
import tempfile
import unittest


class TelegramNoTokenTest(unittest.TestCase):
    def test_telegram_without_credentials_no_traceback(self):
        home = tempfile.mkdtemp(prefix="hc-tg-")
        env = {k: v for k, v in os.environ.items()
               if k not in ("HELLOCHUSQUIS_TELEGRAM_TOKEN", "HELLOCHUSQUIS_TELEGRAM_ALLOW")}
        env["HOME"] = home
        try:
            env["PYTHONUSERBASE"] = site.getuserbase()
            usersite = site.getusersitepackages()
            env["PYTHONPATH"] = usersite + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        except Exception:
            pass
        try:
            p = subprocess.run([sys.executable, "cli.py", "telegram"],
                               capture_output=True, text=True, timeout=60, env=env)
        finally:
            import shutil
            shutil.rmtree(home, ignore_errors=True)
        combined = p.stdout + p.stderr
        self.assertNotIn("Traceback", combined)
        self.assertNotEqual(p.returncode, 0)
