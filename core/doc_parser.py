# DEPRECATED: This module is not used. Consider removing.
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Any


@dataclass
class DocSection:
    title: str
    content: str
    level: int


class DocParser:
    """Parse and generate documentation."""

    def parse_readme(self, content: str) -> list[DocSection]:
        """Parse README content into sections."""
        sections = []
        
        # Split by headers
        lines = content.split('\n')
        current_title = "Introduction"
        current_content = []
        current_level = 1

        for line in lines:
            if match := re.match(r'^(#{1,6})\s+(.+)$', line):
                if current_content:
                    sections.append(DocSection(
                        title=current_title,
                        content='\n'.join(current_content).strip(),
                        level=current_level
                    ))
                
                current_title = match.group(2)
                current_level = len(match.group(1))
                current_content = []
            else:
                current_content.append(line)

        # Add last section
        if current_content:
            sections.append(DocSection(
                title=current_title,
                content='\n'.join(current_content).strip(),
                level=current_level
            ))

        return sections

    def generate_api_docs(self, endpoints: list) -> str:
        """Generate API documentation from endpoints."""
        lines = ["# API Reference", ""]

        for ep in endpoints:
            lines.append(f"## `{ep.method} {ep.path}`")
            lines.append("")
            lines.append(f"{ep.description}")
            lines.append("")

            if ep.params:
                lines.append("### Parameters")
                lines.append("")
                for p in ep.params:
                    lines.append(f"- `{p}`")
                lines.append("")

        return "\n".join(lines)

    def extract_code_examples(self, content: str) -> list[dict]:
        """Extract code examples from markdown."""
        examples = []
        
        # Find fenced code blocks
        pattern = r'```(\w+)?\n(.*?)```'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            lang = match.group(1) or "text"
            code = match.group(2).strip()
            
            examples.append({
                "language": lang,
                "code": code,
                "lines": len(code.split('\n'))
            })

        return examples

    def extract_todos(self, content: str) -> list[str]:
        """Extract TODO items from content."""
        todos = []
        
        for match in re.finditer(r'- \[ \] (.+)|- \[ \] (.+)', content):
            todos.append(match.group(1) or match.group(2))
        
        return todos


def get_parser() -> DocParser:
    return DocParser()