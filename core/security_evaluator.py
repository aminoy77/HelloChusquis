import json
import os
import re
from typing import Dict, Optional
from rich.console import Console

console = Console()


# ---------------------------------------------------------------------------
# Critical-pattern scanner — deterministic, no LLM round-trip
# ---------------------------------------------------------------------------

CRITICAL_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Recursive destructive delete
    (re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-rf\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-fr\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-r\s+-f\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-f\s+-r\b", re.I), "recursive force delete"),
    # Direct root/home wipe
    (re.compile(r"\brm\s+.*/($|/\*)", re.I), "delete root path"),
    (re.compile(r"\brm\s+-[a-zA-Z]*\s+/", re.I), "delete root path"),
    (re.compile(r"\brm\s+-[a-zA-Z]*\s+/home", re.I), "delete home directory"),
    (re.compile(r"\brm\s+-[a-zA-Z]*\s+~", re.I), "delete home directory"),
    # Disk zeroing / raw write
    (re.compile(r"\bdd\s+.*of=/dev/", re.I), "raw disk write"),
    (re.compile(r">\s*/dev/sd", re.I), "raw disk overwrite"),
    (re.compile(r">\s*/dev/nvme", re.I), "raw disk overwrite"),
    # Fork bomb
    (re.compile(r":\(\)\s*\{.*\|.*&", re.I), "fork bomb"),
    # Format
    (re.compile(r"\bmkfs\b", re.I), "filesystem formatting"),
    (re.compile(r"\bformat\b.*\b(c:|/dev/)", re.I), "filesystem formatting"),
    # Dangerous chmod
    (re.compile(r"\bchmod\s+-R\s+777\s+/", re.I), "recursive world-writable on root"),
    # mv root
    (re.compile(r"\bmv\s+/\s+/", re.I), "move root filesystem"),
    # Shutdown / reboot
    (re.compile(r"\bshutdown\b", re.I), "system shutdown"),
    (re.compile(r"\breboot\b", re.I), "system reboot"),
    (re.compile(r"\binit\s+0\b", re.I), "init 0 shutdown"),
    # Partition tools
    (re.compile(r"\b(fdisk|parted|gdisk)\b", re.I), "partition manipulation"),
    # curl|bash / wget|sh (piped remote code)
    (re.compile(r"\bcurl\b.*\|\s*(ba)?sh\b", re.I), "remote code execution via pipe"),
    (re.compile(r"\bwget\b.*\|\s*(ba)?sh\b", re.I), "remote code execution via pipe"),
    (re.compile(r"\bcurl\b.*\|\s*sudo\b", re.I), "remote code execution via pipe as root"),
    # sh -c / bash -c with destructive payload
    (re.compile(r"\b(ba)?sh\s+-c\b.*\b(rm|dd|mkfs|chmod|mv)\b", re.I), "shell -c with destructive command"),
    # python -c / python3 -c with os.system / os.remove
    (re.compile(r"\bpython3?\s+-c\b.*\bos\.(system|remove|rmdir|unlink)\b", re.I), "python inline os destructive call"),
    (re.compile(r"\bpython3?\s+-c\b.*\bsubprocess\b.*\b(rm|dd|mkfs)\b", re.I), "python inline subprocess destructive call"),
    # find -exec with rm/dd
    (re.compile(r"\bfind\b.*-exec\s+(rm|dd)\b", re.I), "find -exec with destructive command"),
    # kill -9 PID 1
    (re.compile(r"\bkill\s+-9\s+1\b", re.I), "kill init process"),
    (re.compile(r"\bkillall\b", re.I), "kill all processes"),
    # sudo + destructive commands
    (re.compile(r"\bsudo\b.*\b(rm\s+-[a-zA-Z]*r[a-zA-Z]*f|dd\s+|mkfs|format|chmod\s+-R\s+777\s+/)\b", re.I), "sudo with destructive command"),
]


def _scan_critical_patterns(command: str) -> Optional[str]:
    """Scan command string for deterministic critical patterns.
    Returns reason string if found, None if clean."""
    for regex, reason in CRITICAL_PATTERNS:
        if regex.search(command):
            return reason
    return None


# ---------------------------------------------------------------------------
# Legacy HIGH_RISK_COMMANDS — kept for backward compat with any callers
# ---------------------------------------------------------------------------

HIGH_RISK_COMMANDS = {
    "rm": ["rf", "fr", "*", "-rf", "-fr"],
    "mv": ["/dev/null"],
    "chmod": [],
    ">": ["/dev/sda*"],
}


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def evaluate_command_safety(command: str, pool=None) -> Dict:
    """Evaluate potential danger of a shell command.

    Deterministic critical-pattern scan runs first (no LLM). LLM fallback
    only for genuinely ambiguous commands. If LLM fails → block.
    Return shape: {"safe": bool, "risk_level": str, "reason": str}
    """
    if not command or not command.strip():
        return {"safe": True, "risk_level": "none"}

    # --- Phase 1: deterministic scan ---
    critical_reason = _scan_critical_patterns(command)
    if critical_reason:
        return {
            "safe": False,
            "risk_level": "critical",
            "reason": f"Deterministic block: {critical_reason}",
        }

    # --- Phase 2: LLM analysis (only for ambiguous cases) ---
    if pool is None:
        # No LLM available — treat as safe if no critical match
        return {"safe": True, "risk_level": "low", "reason": "No dangerous patterns detected"}

    try:
        prompt = f"""
You are a safety filter. A user wants to run this shell command:
COMMAND: `{command}`

Analyze its potential danger. Consider:
- Destructive file operations (rm, dd, mkfs, etc.)
- Privilege escalation or system-level changes
- Network data piped to shell interpreters
- Inline code execution with OS-level side effects

Return ONLY a valid JSON object:
{{"safe": true, "risk_level": "low", "reason": "brief justification"}}

Be conservative — prioritize blocking if unsure — but avoid false positives for harmless commands.
"""
        response = pool.chat_with_retry([{"role": "user", "content": prompt}])
        choices = response.get("choices", [])
        if not choices:
            return {
                "safe": False,
                "risk_level": "critical",
                "reason": "LLM returned no response — blocking as precaution",
            }

        result_text = choices[0].get("message", {}).get("content", "").strip()
        result_text = result_text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(result_text)

        # Ensure required keys exist
        if "safe" not in parsed:
            return {
                "safe": False,
                "risk_level": "critical",
                "reason": "LLM response missing 'safe' field — blocking",
            }
        return parsed

    except json.JSONDecodeError:
        console.print(
            f"[yellow]Warning: Could not parse safety response. "
            f"Blocking command as precaution.[/yellow]"
        )
        return {
            "safe": False,
            "risk_level": "critical",
            "reason": "Failed to parse safety response — blocking as precaution",
        }
    except Exception as e:
        console.print(
            f"[yellow]Warning: Safety validation failed: {e}. "
            f"Blocking command as precaution.[/yellow]"
        )
        return {
            "safe": False,
            "risk_level": "critical",
            "reason": f"Validation failed: {e}",
        }
