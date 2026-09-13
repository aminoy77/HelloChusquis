"""Fase 2: tool skill list/show + prompt section cableada."""
import unittest
from pathlib import Path
import tempfile

from core.skills import SkillRegistry


class FakeAgent:
    def __init__(self, registry):
        self.skills = registry


class SkillToolTest(unittest.TestCase):
    def _agent(self):
        from core.skills import handle_skill_tool
        tmp = Path(tempfile.mkdtemp(prefix="hc-skilltool-"))
        (tmp / "alpha").mkdir()
        (tmp / "alpha" / "SKILL.md").write_text("---\nname: alpha\ndescription: A skill\n---\nBody A\n")
        reg = SkillRegistry(skills_dir=str(tmp / "no-json"))
        reg.discover_skill_md([str(tmp)])
        return FakeAgent(reg), handle_skill_tool

    def test_list_hides_bodies(self):
        agent, handle = self._agent()
        res = handle(agent, {"action": "list"})
        self.assertTrue(res.success)
        self.assertIn("alpha", res.output)
        self.assertNotIn("Body A", res.output)

    def test_show_returns_body(self):
        agent, handle = self._agent()
        res = handle(agent, {"action": "show", "name": "alpha"})
        self.assertTrue(res.success)
        self.assertIn("Body A", res.output)

    def test_show_missing(self):
        agent, handle = self._agent()
        res = handle(agent, {"action": "show", "name": "nope"})
        self.assertFalse(res.success)
