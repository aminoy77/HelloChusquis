"""Fase 2: parse/discover SKILL.md estándar con stdlib."""
import unittest
from pathlib import Path
import tempfile

from core.skills import (
    SkillRegistry, discover_skill_md, parse_skill_md, skills_prompt_section,
)


class SkillMdTest(unittest.TestCase):
    def test_parse_valid(self):
        text = "---\nname: code-review\ndescription: Reviews code\n---\n\n# Code review\nBe strict.\n"
        skill = parse_skill_md(text, source="test")
        self.assertIsNotNone(skill)
        self.assertEqual(skill.name, "code-review")
        self.assertEqual(skill.description, "Reviews code")
        self.assertIn("Be strict", skill.prompt_template)
        self.assertEqual(skill.actions, [])

    def test_parse_invalid(self):
        self.assertIsNone(parse_skill_md("no frontmatter here"))
        self.assertIsNone(parse_skill_md("---\nname: x\n---\n"))  # sin description
        self.assertIsNone(parse_skill_md("---\ndescription: y\n---\nbody"))  # sin name

    def test_name_sanitized(self):
        text = "---\nname: ../../evil\ndescription: d\n---\nbody\n"
        skill = parse_skill_md(text)
        self.assertIsNotNone(skill)
        self.assertNotIn("/", skill.name)
        self.assertNotIn(".", skill.name.replace("-", ""))

    def test_discover_symlink_dir_bypass(self):
        import os
        tmp = Path(tempfile.mkdtemp(prefix="hc-skills-link-"))
        outside = Path(tempfile.mkdtemp(prefix="hc-skills-out-"))
        (outside / "SKILL.md").write_text("---\nname: evil\ndescription: Evil skill\n---\nBody evil\n")
        try:
            os.symlink(outside, tmp / "link")
        except OSError as exc:
            self.skipTest(f"symlink no disponible: {exc}")
        reg = SkillRegistry(skills_dir=str(tmp / "nonexistent-json"))
        n = reg.discover_skill_md([str(tmp)])
        self.assertEqual(n, 0)
        self.assertNotIn("evil", [s["name"] for s in reg.list_skills()])

    def test_parse_folded_description(self):
        text = "---\nname: hyperframes\ndescription: >\n  First line\n  second line\n---\nBody\n"
        skill = parse_skill_md(text)
        self.assertIsNotNone(skill)
        self.assertEqual(skill.description, "First line second line")
        text_lit = "---\nname: x\ndescription: |-\n  line one\n  line two\n---\nBody\n"
        skill_lit = parse_skill_md(text_lit)
        self.assertIsNotNone(skill_lit)
        self.assertEqual(skill_lit.description, "line one\nline two")

    def test_discover_and_section(self):
        tmp = Path(tempfile.mkdtemp(prefix="hc-skills-"))
        (tmp / "alpha").mkdir()
        (tmp / "alpha" / "SKILL.md").write_text("---\nname: alpha\ndescription: A skill\n---\nBody A\n")
        (tmp / "broken").mkdir()
        (tmp / "broken" / "SKILL.md").write_text("garbage")
        reg = SkillRegistry(skills_dir=str(tmp / "nonexistent-json"))
        n = reg.discover_skill_md([str(tmp)])
        self.assertEqual(n, 1)
        self.assertIn("alpha", [s["name"] for s in reg.list_skills()])
        section = reg.skills_prompt_section()
        self.assertIn("alpha", section)
