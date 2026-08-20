"""Regression tests for safe skill action execution."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from core.skills import Skill, SkillRegistry


class TestSkillRegistryExecutionSecurity(unittest.TestCase):
    def test_shell_skill_requires_explicit_approval_before_execution(self):
        registry = SkillRegistry(skills_dir="/nonexistent")
        registry.register(Skill(name="danger", description="", actions=[{"type": "shell", "command": "echo hi"}]))

        with patch("core.skills.subprocess.run") as run:
            result = registry.execute_skill("danger", {})

        self.assertFalse(result["success"])
        self.assertIn("approval", result["error"].lower())
        run.assert_not_called()

    def test_approved_shell_skill_uses_isolated_non_shell_process(self):
        registry = SkillRegistry(skills_dir="/nonexistent")
        registry.register(
            Skill(
                name="safe",
                description="",
                requires_approval=True,
                actions=[{"type": "shell", "command": "echo {value}", "timeout": 9999}],
            )
        )
        completed = SimpleNamespace(returncode=0, stdout="ok", stderr="")

        with patch("core.skills.subprocess.run", return_value=completed) as run:
            result = registry.execute_skill("safe", {"value": "hello", "approved": True})

        self.assertTrue(result["success"])
        self.assertEqual(run.call_args.args[0], ["echo", "hello"])
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertNotIn("OPENAI_API_KEY", run.call_args.kwargs["env"])
        self.assertEqual(run.call_args.kwargs["timeout"], 60)


if __name__ == "__main__":
    unittest.main()
