"""Fase 2: CLI skills list/show en frío (HOME tmp)."""
import os
import site
import subprocess
import sys
import tempfile
import unittest


class CliSkillsTest(unittest.TestCase):
    def _run_cold(self, cmd):
        home = tempfile.mkdtemp(prefix="hc-skills-cli-")
        env = dict(os.environ, HOME=home)
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

    def test_skills_list_cold(self):
        p = self._run_cold([sys.executable, "cli.py", "skills", "list"])
        self.assertNotIn("Traceback", p.stderr)
        self.assertEqual(p.returncode, 0, f"exit!=0: {p.stderr[-500:]}")
        # HOME tmp no aporta skills, pero el repo puede descubrir .agents/skills
        # (gitignored: existe aquí, ausente en checkout limpio). Ambos valen:
        # hint de instalación o líneas "- name: desc".
        self.assertTrue(
            "~/.hellochusquis/skills" in p.stdout or ": " in p.stdout,
            f"sin contenido útil: {p.stdout[:500]}",
        )
