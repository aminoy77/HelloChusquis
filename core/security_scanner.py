from __future__ import annotations
import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SecurityFinding:
    severity: str  # critical, high, medium, low, info
    category: str
    description: str
    file: str
    line: int = 0
    recommendation: str = ""


class SecurityScanner:
    """Scan code for security vulnerabilities."""

    # Common vulnerability patterns
    PATTERNS = {
        "hardcoded_secret": {
            "pattern": r"(api_key|apikey|secret|password|token)\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]",
            "severity": "critical",
            "description": "Hardcoded secret detected"
        },
        "sql_injection": {
            "pattern": r"(execute|exec|cursor\.execute)\s*\([^)]*\%s[^)]*\)",
            "severity": "high",
            "description": "Potential SQL injection vulnerability"
        },
        "eval_usage": {
            "pattern": r"\beval\s*\(",
            "severity": "high",
            "description": "Use of eval() is dangerous"
        },
        "pickle_load": {
            "pattern": r"pickle\.load\s*\(",
            "severity": "high",
            "description": "pickle.load() can execute arbitrary code"
        },
        "command_injection": {
            "pattern": r"(os\.system|os\.popen|subprocess\.call|subprocess\.run)\s*\([^)]*\+",
            "severity": "critical",
            "description": "Potential command injection"
        },
        "weak_crypto": {
            "pattern": r"(md5|sha1)\s*\(",
            "severity": "medium",
            "description": "Weak cryptographic hash function"
        },
        "insecure_random": {
            "pattern": r"random\.random\s*\(",
            "severity": "low",
            "description": "random() is not cryptographically secure"
        },
        "debug_mode": {
            "pattern": r"DEBUG\s*=\s*True",
            "severity": "medium",
            "description": "Debug mode enabled in production"
        },
        "todo_comment": {
            "pattern": r"#\s*TODO\s*:",
            "severity": "info",
            "description": "TODO comment found"
        },
        "password_in_url": {
            "pattern": r"https?://[^:]+:[^@]+@",
            "severity": "high",
            "description": "Credentials in URL detected"
        }
    }

    def __init__(self):
        self.findings: list[SecurityFinding] = []

    def scan_file(self, file_path: str) -> list[SecurityFinding]:
        """Scan a single file for security issues."""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            return findings

        import re
        
        for rule_id, rule in self.PATTERNS.items():
            pattern = rule["pattern"]
            
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    finding = SecurityFinding(
                        severity=rule["severity"],
                        category=rule_id,
                        description=rule["description"],
                        file=file_path,
                        line=i,
                        recommendation=self._get_recommendation(rule_id)
                    )
                    findings.append(finding)

        return findings

    def scan_directory(self, root_path: str, extensions: list = None) -> list[SecurityFinding]:
        """Scan entire directory recursively."""
        extensions = extensions or ['.py', '.js', '.ts', '.java', '.go', '.rb', '.php']
        findings = []
        
        root = Path(root_path)
        
        # Ignore directories
        ignore = {'.git', 'node_modules', '__pycache__', 'venv', '.venv', 'dist', 'build'}
        
        for ext in extensions:
            for file in root.rglob(f"*{ext}"):
                # Skip ignored directories
                if any(ig in file.parts for ig in ignore):
                    continue
                    
                try:
                    findings.extend(self.scan_file(str(file)))
                except Exception:
                    pass
        
        self.findings = findings
        return findings

    def _get_recommendation(self, category: str) -> str:
        """Get recommendation for a finding."""
        recommendations = {
            "hardcoded_secret": "Use environment variables or a secrets manager instead",
            "sql_injection": "Use parameterized queries or an ORM",
            "eval_usage": "Use ast.literal_eval or json.loads instead",
            "pickle_load": "Use JSON or a safe serialization format",
            "command_injection": "Validate and sanitize all user input",
            "weak_crypto": "Use hashlib.sha256 or hashlib.blake2 instead",
            "insecure_random": "Use secrets module for cryptographic randomness",
            "debug_mode": "Set DEBUG=False in production",
            "password_in_url": "Use authentication headers instead"
        }
        return recommendations.get(category, "Review and fix this issue")

    def generate_report(self) -> str:
        """Generate a security report."""
        if not self.findings:
            return "✅ No security issues found!"

        # Group by severity
        critical = [f for f in self.findings if f.severity == "critical"]
        high = [f for f in self.findings if f.severity == "high"]
        medium = [f for f in self.findings if f.severity == "medium"]
        low = [f for f in self.findings if f.severity == "low"]
        info = [f for f in self.findings if f.severity == "info"]

        lines = [f"🔒 Security Report ({len(self.findings)} issues found)", ""]

        if critical:
            lines.append(f"❌ Critical: {len(critical)}")
            for f in critical[:3]:
                lines.append(f"  {f.file}:{f.line} - {f.description}")

        if high:
            lines.append(f"⚠️ High: {len(high)}")
            for f in high[:3]:
                lines.append(f"  {f.file}:{f.line} - {f.description}")

        if medium:
            lines.append(f"⚡ Medium: {len(medium)}")
            for f in medium[:2]:
                lines.append(f"  {f.file}:{f.line} - {f.description}")

        if low or info:
            lines.append(f"ℹ️ Low/Info: {len(low) + len(info)}")

        return "\n".join(lines)

    def to_json(self) -> str:
        """Export findings as JSON."""
        return json.dumps([
            {
                "severity": f.severity,
                "category": f.category,
                "description": f.description,
                "file": f.file,
                "line": f.line,
                "recommendation": f.recommendation
            }
            for f in self.findings
        ], indent=2)


def get_scanner() -> SecurityScanner:
    return SecurityScanner()