from __future__ import annotations
import subprocess
import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class CodeIssue:
    severity: str
    line: int
    column: int
    message: str
    rule: str
    tool: str


class CodeAnalyzer:
    """Real-time code analysis with multiple linters."""

    def __init__(self):
        self.tools = ["ruff", "mypy", "eslint", "black"]
        self._available = self._detect_tools()

    def _detect_tools(self) -> dict:
        available = {}
        for tool in self.tools:
            try:
                subprocess.run([tool, "--version"], capture_output=True, timeout=5)
                available[tool] = True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                available[tool] = False
        return available

    def analyze(self, file_path: str, language: str = "python") -> list[CodeIssue]:
        issues = []
        issues.extend(self._ruff_check(file_path))
        issues.extend(self._mypy_check(file_path))
        return issues

    def _ruff_check(self, file_path: str) -> list[CodeIssue]:
        if not self._available.get("ruff"):
            return []
        try:
            result = subprocess.run(
                ["ruff", "check", file_path, "--output-format=json"],
                capture_output=True, text=True, timeout=30
            )
            issues = []
            if result.stdout:
                data = json.loads(result.stdout)
                for item in data:
                    issues.append(CodeIssue(
                        severity=item.get("severity", "error"),
                        line=item.get("location", {}).get("row", 0),
                        column=item.get("location", {}).get("column", 0),
                        message=item.get("message", ""),
                        rule=item.get("rule", ""),
                        tool="ruff"
                    ))
            return issues
        except Exception:
            return []

    def _mypy_check(self, file_path: str) -> list[CodeIssue]:
        if not self._available.get("mypy"):
            return []
        try:
            result = subprocess.run(
                ["mypy", file_path, "--json-output"],
                capture_output=True, text=True, timeout=60
            )
            issues = []
            if result.stdout:
                data = json.loads(result.stdout)
                for item in data.get("messages", []):
                    issues.append(CodeIssue(
                        severity="error",
                        line=item.get("line", 0),
                        column=item.get("column", 0),
                        message=item.get("message", ""),
                        rule=item.get("code", ""),
                        tool="mypy"
                    ))
            return issues
        except Exception:
            return []

    def analyze_and_fix(self, file_path: str) -> dict:
        """Run analysis and auto-fix if possible."""
        issues = self.analyze(file_path)
        fixes_applied = []

        if self._available.get("ruff"):
            try:
                result = subprocess.run(
                    ["ruff", "check", file_path, "--fix"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    fixes_applied.append("Ruff auto-fix applied")
            except Exception:
                pass

        if self._available.get("black"):
            try:
                result = subprocess.run(
                    ["black", file_path],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    fixes_applied.append("Black formatting applied")
            except Exception:
                pass

        return {
            "issues": [vars(i) for i in issues],
            "fixes": fixes_applied,
            "clean": len(issues) == 0
        }

    def generate_report(self, file_path: str) -> str:
        """Generate a human-readable analysis report."""
        results = self.analyze_and_fix(file_path)
        if results["clean"]:
            return f"✅ {file_path} - No issues found!"

        lines = [f"🔍 Analysis of {file_path}"]

        if results["fixes"]:
            lines.append("✓ Fixes applied:")
            for fix in results["fixes"]:
                lines.append(f"  - {fix}")

        if results["issues"]:
            errors = [i for i in results["issues"] if i["severity"] == "error"]
            warnings = [i for i in results["issues"] if i["severity"] == "warning"]

            if errors:
                lines.append(f"\n❌ {len(errors)} errors:")
                for e in errors:
                    lines.append(f"  L{e['line']}: {e['message']}")

            if warnings:
                lines.append(f"\n⚠️ {len(warnings)} warnings:")
                for w in warnings:
                    lines.append(f"  L{w['line']}: {w['message']}")

        return "\n".join(lines)


def get_analyzer() -> CodeAnalyzer:
    return CodeAnalyzer()