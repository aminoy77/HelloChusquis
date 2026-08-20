"""Regression tests for non-interactive startup and provider configuration."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.provider import ProviderPool
from core.runtime import AgentNotReadyError, AgentRuntime
from core.setup import ensure_config


LOCAL_PROVIDER_CONFIG = {
    "providers": [
        {
            "name": "Ollama (local)",
            "base_url": "http://localhost:11434/v1",
            "api_key": "",
            "model": "llama3.2",
            "priority": 1,
        }
    ],
    "settings": {
        "provider_reset_hours": 2,
        "timeout_seconds": 30,
        "workspace_dirs": ["/tmp/workspace"],
    },
    "agent": {"system_prompt": "x" * 120},
}


class TestNonInteractiveConfiguration(unittest.TestCase):
    def test_missing_config_does_not_open_setup_wizard(self):
        """Service startup receives a normal exception instead of prompting."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch("core.setup.Path.home", return_value=Path(tmp_dir)):
                with self.assertRaisesRegex(FileNotFoundError, "hellochusquis setup"):
                    ensure_config(interactive=False)


class TestProviderPoolConfiguration(unittest.TestCase):
    def test_uses_explicit_config_without_reloading_disk(self):
        pool = ProviderPool(config=LOCAL_PROVIDER_CONFIG)

        self.assertEqual(len(pool.providers), 1)
        self.assertEqual(pool.providers[0].name, "Ollama (local)")
        self.assertEqual(pool.timeout, 30)
        self.assertEqual(pool.reset_after_seconds, 7200)

    def test_loads_local_only_config_without_api_key(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.yaml"
            config_path.write_text(
                """providers:
  - name: Ollama (local)
    base_url: http://localhost:11434/v1
    api_key: ''
    model: llama3.2
    priority: 1
settings:
  timeout_seconds: 20
"""
            )

            pool = ProviderPool(config_path=config_path)

        self.assertEqual(len(pool.providers), 1)
        self.assertEqual(pool.providers[0].api_key, "")
        self.assertEqual(pool.timeout, 20)


class _FakePool:
    def status(self):
        return [{"name": "Test", "status": "ready"}]


class _FakeAgent:
    def __init__(self, config, require_approval=False):
        self.config = config
        self.require_approval = require_approval
        self.pool = _FakePool()
        self.dispose_calls = 0

    def dispose_session(self):
        self.dispose_calls += 1


class TestAgentRuntime(unittest.TestCase):
    def test_failed_initialization_keeps_runtime_inspectable(self):
        runtime = AgentRuntime(
            config_loader=lambda interactive: (_ for _ in ()).throw(
                FileNotFoundError("missing config")
            ),
            agent_factory=_FakeAgent,
        )

        self.assertFalse(runtime.is_ready)
        self.assertEqual(runtime.provider_status(), [])
        self.assertFalse(runtime.readiness()["ready"])
        with self.assertRaises(AgentNotReadyError):
            runtime.get()

    def test_successful_initialization_reports_readiness(self):
        runtime = AgentRuntime(
            config_loader=lambda interactive: {"provider": "test"},
            agent_factory=_FakeAgent,
        )

        self.assertTrue(runtime.is_ready)
        self.assertEqual(runtime.get().config, {"provider": "test"})
        self.assertTrue(runtime.get().require_approval)
        self.assertTrue(runtime.readiness()["ready"])

    def test_sessions_receive_distinct_agents_and_reuse_their_own_history(self):
        runtime = AgentRuntime(
            config_loader=lambda interactive: {"provider": "test"},
            agent_factory=_FakeAgent,
            max_sessions=2,
        )

        alpha = runtime.get("alpha")
        beta = runtime.get("beta")

        self.assertIsNot(alpha, beta)
        self.assertIs(alpha, runtime.get("alpha"))
        self.assertEqual(runtime.session_count, 2)

    def test_session_cache_evicts_least_recently_used_agent(self):
        runtime = AgentRuntime(
            config_loader=lambda interactive: {"provider": "test"},
            agent_factory=_FakeAgent,
            max_sessions=2,
        )

        alpha = runtime.get("alpha")
        runtime.get("beta")
        runtime.get("gamma")

        self.assertEqual(runtime.session_count, 2)
        self.assertEqual(alpha.dispose_calls, 1)
        self.assertIsNot(alpha, runtime.get("alpha"))

    def test_refresh_clears_cached_sessions(self):
        runtime = AgentRuntime(
            config_loader=lambda interactive: {"provider": "test"},
            agent_factory=_FakeAgent,
        )
        default_before_reload = runtime.get()
        before_reload = runtime.get("alpha")

        self.assertTrue(runtime.refresh())
        self.assertEqual(runtime.session_count, 0)
        self.assertEqual(default_before_reload.dispose_calls, 1)
        self.assertEqual(before_reload.dispose_calls, 1)
        self.assertIsNot(before_reload, runtime.get("alpha"))


if __name__ == "__main__":
    unittest.main()
