"""Fase 1: web y api boot + /health sin traceback."""
import os
import site
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.request


def _free(port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def _wait_health(url, timeout_s=25):
    end = time.time() + timeout_s
    while time.time() < end:
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                if r.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


class SurfaceBootTest(unittest.TestCase):
    def _boot(self, surface, port):
        if not _free(port):
            self.skipTest(f"puerto {port} ocupado")
        home = tempfile.mkdtemp(prefix="hc-boot-")
        env = dict(os.environ, HOME=home, HELLOCHUSQUIS_API_KEY="fase1-smoke-key")
        try:
            env["PYTHONUSERBASE"] = site.getuserbase()
            usersite = site.getusersitepackages()
            env["PYTHONPATH"] = usersite + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
        except Exception:
            pass
        cmd = [sys.executable, "cli.py", surface, "--port", str(port), "--no-browser"]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             text=True, env=env)
        return p, home

    def _stop(self, p, home):
        import shutil
        try:
            p.terminate()
            p.wait(timeout=15)
        except Exception:
            p.kill()
        out = p.stdout.read() if p.stdout else ""
        shutil.rmtree(home, ignore_errors=True)
        return out

    def test_web_boot_health(self):
        p, home = self._boot("web", 18080)
        try:
            self.assertTrue(_wait_health("http://127.0.0.1:18080/health"), "web sin /health 200")
        finally:
            out = self._stop(p, home)
        self.assertNotIn("Traceback", out)

    def test_api_boot_health(self):
        p, home = self._boot("api", 18081)
        try:
            self.assertTrue(_wait_health("http://127.0.0.1:18081/health"), "api sin /health 200")
        finally:
            out = self._stop(p, home)
        self.assertNotIn("Traceback", out)
