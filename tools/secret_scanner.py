from tools.base import BaseTool, ToolResult
import os
import re


PLUGIN_NAME = "secret_scanner"
PLUGIN_DESCRIPTION = "Scan code for secrets, API keys, and sensitive data"

SECRET_SCANNER_SCHEMA = {
    "type": "function",
    "function": {
        "name": "secret_scanner",
        "description": "Scan code for exposed secrets, API keys, and sensitive information",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["scan", "check_file", "check_env"],
                    "description": "Scan action"
                },
                "path": {"type": "string", "description": "Directory or file to scan"},
                "severity": {"type": "string", "description": "Severity level filter"},
            },
            "required": ["action"]
        }
    }
}


SECRET_PATTERNS = {
    "AWS_ACCESS_KEY": (r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ASIA)[A-Z0-9]{16}", "critical"),
    "AWS_SECRET": (r"(?i)aws(.{0,20})?(?-i)secret(.{0,20})?['\"=:\s]+['\"][A-Za-z0-9/+=]{40}['\"]", "critical"),
    "GITHUB_TOKEN": (r"gh[pousr]_[A-Za-z0-9]{36,255}", "critical"),
    "SLACK_TOKEN": (r"xox[baprs]-([0-9a-zA-Z]{10,48})", "critical"),
    "GOOGLE_API": (r"AIza[0-9A-Za-z_-]{35}", "high"),
    "OPENAI_KEY": (r"sk-[A-Za-z0-9]{32,}", "critical"),
    "ANTHROPIC_KEY": (r"sk-ant-api0[0-9A-Za-z_-]{50,}", "critical"),
    "STRIPE_KEY": (r"sk_live_[0-9a-zA-Z]{24,}", "critical"),
    "JWT_SECRET": (r"jwt[._-]?secret[._-]?['\"=:\s]+['\"][A-Za-z0-9-_=]{10,}['\"]", "high"),
    "PRIVATE_KEY": (r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----", "critical"),
    "DATABASE_URL": (r"(?i)(mysql|postgres|postgresql|mongodb)://[^:]+:[^@]+@", "high"),
    "BEARER_TOKEN": (r"Bearer [A-Za-z0-9\-._~+/]+=*", "medium"),
    "NPM_TOKEN": (r"npm_[A-Za-z0-9]{36}", "high"),
    "DOCKERHUB_TOKEN": (r"dockerhub[_-]?token[=:\s]+['\"][A-Za-z0-9]{20,}['\"]", "high"),
}


def scan_file(filepath: str) -> list:
    """Scan a single file for secrets."""
    findings = []
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            lines = content.split("\n")
            
            for pattern_name, (pattern, severity) in SECRET_PATTERNS.items():
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    # Find line number
                    line_num = content[:match.start()].count("\n") + 1
                    line = lines[line_num - 1] if line_num <= len(lines) else ""
                    
                    findings.append({
                        "file": filepath,
                        "line": line_num,
                        "type": pattern_name,
                        "severity": severity,
                        "match": match.group()[:50] + "...",
                        "context": line.strip()[:100]
                    })
    except Exception:
        pass
    
    return findings


def run(action: str, path: str = "", severity: str = "") -> str:
    """Scan for secrets."""
    if not path:
        return "Error: path required"
    
    if not os.path.exists(path):
        return f"Error: Path not found: {path}"
    
    findings = []
    
    if action == "scan":
        if os.path.isfile(path):
            findings = scan_file(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                # Skip hidden and common ignore dirs
                dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "venv", ".git")]
                
                for file in files:
                    if file.endswith((".js", ".ts", ".py", ".json", ".yaml", ".yml", ".env", ".sh", ".rb", ".go")):
                        filepath = os.path.join(root, file)
                        findings.extend(scan_file(filepath))
    
    elif action == "check_file":
        findings = scan_file(path)
    
    elif action == "check_env":
        # Check environment variables
        import os
        for key, value in os.environ.items():
            for pattern_name, (pattern, sev) in SECRET_PATTERNS.items():
                if re.search(pattern, value, re.IGNORECASE):
                    findings.append({
                        "file": "ENV",
                        "line": 0,
                        "type": pattern_name,
                        "severity": sev,
                        "match": f"ENV_VAR: {key}",
                        "context": f"{key}={value[:20]}..."
                    })
    
    # Filter by severity
    if severity:
        findings = [f for f in findings if f["severity"] == severity]
    
    if not findings:
        return "✓ No secrets found!"
    
    # Format results
    result = [f"🚨 Found {len(findings)} potential secret(s):\n"]
    
    for f in findings:
        emoji = "🔴" if f["severity"] == "critical" else "🟠" if f["severity"] == "high" else "🟡"
        result.append(f"{emoji} [{f['severity'].upper()}] {f['type']}")
        result.append(f"   File: {f['file']}:{f['line']}")
        result.append(f"   Match: {f['match']}")
        result.append("")
    
    return "\n".join(result)


if __name__ == "__main__":
    print("Secret scanner plugin loaded.")