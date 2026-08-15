"""Regression tests for web auth middleware bootstrap routes."""
import importlib.util
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


class _DummyPool:
    def status(self):
        return [{"status": "ready", "name": "dummy", "model": "dummy-model"}]


class _DummyHistory:
    def clear(self):
        return None

    def get(self):
        return []


class _DummyAgent:
    def __init__(self, _config):
        self.pool = _DummyPool()
        self.plugins = []
        self.history = _DummyHistory()

    def run(self, message):
        return f"ok:{message}"


def _load_web_server_module(module_name: str):
    repo_root = Path(__file__).resolve().parents[1]
    module_path = repo_root / "web" / "server.py"

    setup_mod = types.ModuleType("core.setup")
    setup_mod.ensure_config = lambda: {"settings": {}}

    agent_mod = types.ModuleType("core.agent")
    agent_mod.Agent = _DummyAgent

    plugins_mod = types.ModuleType("core.plugins")
    plugins_mod.load_plugins = lambda: []

    db_memory_mod = types.ModuleType("core.db_memory")
    db_memory_mod.load_summary = lambda: ""

    learning_mod = types.ModuleType("core.learning")
    learning_mod.load_learnings = lambda: {}

    stubs = {
        "core.setup": setup_mod,
        "core.agent": agent_mod,
        "core.plugins": plugins_mod,
        "core.db_memory": db_memory_mod,
        "core.learning": learning_mod,
    }

    with patch.dict(sys.modules, stubs):
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        return module


class TestWebAuthMiddleware(unittest.TestCase):
    def test_auth_bootstrap_routes_are_public_when_auth_enabled(self):
        with patch.dict(os.environ, {"HELLOCHUSQUIS_API_KEY": "secret-token"}, clear=False):
            module = _load_web_server_module("web_server_auth_enabled")
            client = TestClient(module.app)

            check = client.get("/auth/check")
            self.assertEqual(check.status_code, 200)
            self.assertTrue(check.json()["auth_required"])

            verify = client.post("/auth/verify", json={"message": "secret-token"})
            self.assertEqual(verify.status_code, 200)
            self.assertEqual(verify.json()["status"], "ok")

            blocked = client.post("/chat", json={"message": "hello"})
            self.assertEqual(blocked.status_code, 401)


if __name__ == "__main__":
    unittest.main()
