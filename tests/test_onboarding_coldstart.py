"""Fase 1: comandos fríos con HOME vacío no hacen traceback."""
import os
import site
import subprocess
import sys
import tempfile
import unittest

CMDS = [
    [sys.executable, "cli.py", "version"],
    [sys.executable, "cli.py", "--help"],
    [sys.executable, "cli.py", "config", "--show"],
    [sys.executable, "cli.py", "knowledge"],
]


class ColdStartTest(unittest.TestCase):
    def _run_cold(self, cmd):
        home = tempfile.mkdtemp(prefix="hc-cold-")
        env = dict(os.environ, HOME=home)
        # Deps viven en user-site del HOME real; con HOME aislado queda
        # invisible. Reexponer solo lectura sin escribir en HOME real.
        try:
            env["PYTHONUSERBASE"] = site.getuserbase()
            usersite = site.getusersitepackages()
            env["PYTHONPATH"] = usersite + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        except Exception:
            pass
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=90, env=env)
        finally:
            import shutil
            shutil.rmtree(home, ignore_errors=True)
        return p

    def test_cold_commands_no_traceback(self):
        for cmd in CMDS:
            with self.subTest(cmd=cmd):
                p = self._run_cold(cmd)
                self.assertNotIn("Traceback", p.stderr, f"traceback en: {cmd}")
                self.assertEqual(p.returncode, 0, f"exit!=0 en {cmd}: {p.stderr[-500:]}")

    def test_help_lists_surfaces(self):
        p = self._run_cold([sys.executable, "cli.py", "--help"])
        for word in ("web", "api", "telegram", "doctor", "config"):
            self.assertIn(word, p.stdout)
