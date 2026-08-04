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
    # Recursive destructive delete (short flags, case variants)
    (re.compile(r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-[a-zA-Z]*f[a-zA-Z]*r\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-rf\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-fr\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-r\s+-f\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-f\s+-r\b", re.I), "recursive force delete"),
    # rm long-form / mixed / cluster flag combos (--recursive --force, -r --force,
    # --recursive -f, -rfX where X is anything, -Rf / -fR / -rF case variants)
    (re.compile(r"\brm\s+--recursive\s+--force\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+--force\s+--recursive\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+--recursive\s+-[a-zA-Z]*[fF]\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+--force\s+-[a-zA-Z]*[rR]\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-[a-zA-Z]*[fF]\s+--recursive\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-[a-zA-Z]*[rR]\s+--force\b", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*[fF]", re.I), "recursive force delete"),
    (re.compile(r"\brm\s+-[a-zA-Z]*[fF][a-zA-Z]*[rR]", re.I), "recursive force delete"),
    # Direct root/home wipe
    (re.compile(r"\brm\s+.*/($|/\*)", re.I), "delete root path"),
    (re.compile(r"\brm\s+-[a-zA-Z]*\s+/", re.I), "delete root path"),
    (re.compile(r"\brm\s+-[a-zA-Z]*\s+/home", re.I), "delete home directory"),
    (re.compile(r"\brm\s+-[a-zA-Z]*\s+~", re.I), "delete home directory"),
    # Disk zeroing / raw write
    (re.compile(r"\bdd\s+.*of=/dev/", re.I), "raw disk write"),
    (re.compile(r">\s*/dev/sd", re.I), "raw disk overwrite"),
    (re.compile(r">\s*/dev/nvme", re.I), "raw disk overwrite"),
    # Fork bomb — classic colon form
    (re.compile(r":\(\)\s*\{.*\|.*&", re.I), "fork bomb"),
    # Fork bomb — renamed form: ANY NAME(){ NAME|NAME& };NAME
    (re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{[^{}]*\b\1\s*\|\s*\1\b[^{}]*&\s*\}", re.I), "fork bomb"),
    # Format
    (re.compile(r"\bmkfs\b", re.I), "filesystem formatting"),
    (re.compile(r"\bmke2fs\b", re.I), "filesystem formatting"),
    (re.compile(r"\bnewfs_\w+\b", re.I), "filesystem formatting"),
    (re.compile(r"\bdiskutil\s+(erase\S*|zero\w*|secureErase\S*)\b", re.I), "filesystem formatting"),
    (re.compile(r"\bformat\b.*\b(c:|/dev/)", re.I), "filesystem formatting"),
    # Dangerous chmod (recursive world-writable / symbolic rwx on /)
    (re.compile(r"\bchmod\s+-R\s+777\s+/", re.I), "recursive world-writable on root"),
    (re.compile(r"\bchmod\s+(?:--recursive\s+|-r[a-zA-Z]*\s+)?(0?7777?|[ugoa]*[+-=][rwxXugoa]*)(?:\s+(?:--recursive|-r[a-zA-Z]*))?\s+/(?:\s|$)", re.I), "world-writable on root"),
    # mv root
    (re.compile(r"\bmv\s+/\s+/", re.I), "move root filesystem"),
    # Shutdown / reboot / power-off equivalents
    (re.compile(r"\bshutdown\b", re.I), "system shutdown"),
    (re.compile(r"\breboot\b", re.I), "system reboot"),
    (re.compile(r"\binit\s+0\b", re.I), "init 0 shutdown"),
    (re.compile(r"^\s*(sudo\s+)?(halt|poweroff)\b", re.I), "system shutdown"),
    (re.compile(r"\bsystemctl\s+(halt|poweroff|reboot)\b", re.I), "system shutdown"),
    (re.compile(r"\bosascript\b.*\b(shut\s?down|restart)\b", re.I), "system shutdown via osascript"),
    (re.compile(r"\btelinit\s+[06]\b", re.I), "runlevel shutdown"),
    # Partition tools
    (re.compile(r"\b(fdisk|parted|gdisk)\b", re.I), "partition manipulation"),
    # curl|bash / wget|sh (piped remote code)
    (re.compile(r"\bcurl\b.*\|\s*(ba)?sh\b", re.I), "remote code execution via pipe"),
    (re.compile(r"\bwget\b.*\|\s*(ba)?sh\b", re.I), "remote code execution via pipe"),
    (re.compile(r"\bcurl\b.*\|\s*sudo\b", re.I), "remote code execution via pipe as root"),
    # Two-stage RCE: download to file, then execute
    (re.compile(r"\bcurl\b[^;&|\n]*(?:-o|-O|--output|--output-document|--remote-name)[^;&|\n]*(?:&&|;|\n)\s*((ba)?sh|zsh|fish)\b", re.I), "download and execute"),
    (re.compile(r"\bwget\b[^;&|\n]*(?:-O|-o|--output-document)[^;&|\n]*(?:&&|;|\n)\s*((ba)?sh|zsh|fish)\b", re.I), "download and execute"),
    # RCE via process substitution: bash <(curl ...)
    (re.compile(r"\b((ba)?sh|zsh|fish)\s*<\(\s*(curl|wget)\b", re.I), "remote code via process substitution"),
    (re.compile(r"\b(source|\.)\s*<\(\s*(curl|wget)\b", re.I), "remote code via process substitution"),
    # RCE via xargs: curl ... | xargs -I{} sh -c {}
    (re.compile(r"\b(curl|wget)\b.*\|\s*xargs\b.*\b(sh|bash|zsh|fish|python)\b", re.I), "remote code via xargs"),
    (re.compile(r"\b(curl|wget)\b.*\|\s*xargs\b.*\b(rm|dd|mkfs|chmod|mv|shutdown)\b", re.I), "remote code via xargs"),
    # sh -c / bash -c with destructive payload (extended keyword list)
    (re.compile(r"\b((ba)?sh|zsh|fish)\s+(--command|-c)\b.*\b(rm|dd|mkfs|mke2fs|mv|chmod|chown|shutdown|reboot|halt|poweroff|kill|fdisk|parted|curl|wget)\b", re.I), "shell -c with destructive command"),
    # python -c / python3 -c inline code execution (import os/shutil/subprocess,
    # from pathlib, os.* destructive calls, shutil.*, rmtree, unlink)
    (re.compile(r"\bpython3?\s+-c\b.*(?:\bimport\s+(?:os|shutil|subprocess)\b|\bfrom\s+pathlib\b|\bos\.(?:system|remove|rmdir|unlink|popen)\b|\bshutil\.\w+|\brmtree\s*\(|\.unlink\s*\()", re.I), "python inline code execution"),
    # find -exec with rm/dd
    (re.compile(r"\bfind\b.*-exec\s+(rm|dd)\b", re.I), "find -exec with destructive command"),
    # find -delete rooted at /, /home, or ~
    (re.compile(r"\bfind\s+(?:/|/home|~)(?:\s)[^;&|\n]*-delete\b", re.I), "recursive delete via find"),
    # kill critical PIDs (init=1, process group=0, everything=-1)
    (re.compile(r"\bkill\s+-(SIG)?\w+\s+(-?1|0)\b", re.I), "kill critical process"),
    (re.compile(r"\bkill\s+-s\s+(SIG)?\w+\s+(-?1|0)\b", re.I), "kill critical process"),
    (re.compile(r"\bkill\s+-1\b(?=\s*(?:$|[;&|\n]))", re.I), "kill all processes"),
    (re.compile(r"\bkillall\b", re.I), "kill all processes"),
    # sudo + destructive commands
    (re.compile(r"\bsudo\b.*\b(rm\s+-[a-zA-Z]*r[a-zA-Z]*f|dd\s+|mkfs|format|chmod\s+-R\s+777\s+/)\b", re.I), "sudo with destructive command"),
]


# ---------------------------------------------------------------------------
# Token-level destructive scan — catches combos regex can't express cleanly
# ---------------------------------------------------------------------------

_CMD_SEGMENT_RE = re.compile(r"[;&|\n]")


def _is_rm_root_target(arg: str) -> bool:
    """True if an rm target is a root-ish path (whole-dir wipe)."""
    return (
        arg in ("/", "~", "/home")
        or arg.endswith("/*")
        or arg.endswith("/")
    )


def _scan_rm_destructive(command: str) -> Optional[str]:
    """Token-level rm scan.

    Catches recursive+force regardless of form:
      rm -rfX, rm -frX, rm -Rf, rm -fR, rm -rF,
      rm --recursive --force, rm --force --recursive,
      rm -r --force, rm --force -r, rm --recursive -f, rm -f --recursive
    Also rm with any flags (or none) targeting /, /home, ~.
    """
    for segment in _CMD_SEGMENT_RE.split(command):
        if not re.search(r"\brm\b", segment):
            continue
        tokens = segment.split()
        rm_idx = next((i for i, t in enumerate(tokens) if t == "rm"), None)
        if rm_idx is None:
            continue
        has_rec = False
        has_force = False
        root_target = False
        for arg in tokens[rm_idx + 1:]:
            if arg == "--":
                break
            if arg in ("--recursive", "-r", "-R"):
                has_rec = True
            elif arg in ("--force", "-f", "-F"):
                has_force = True
            elif arg.startswith("-") and not arg.startswith("--"):
                low = arg.lower()
                if "r" in low:
                    has_rec = True
                if "f" in low:
                    has_force = True
            elif _is_rm_root_target(arg):
                root_target = True
        if has_rec and has_force:
            return "recursive force delete"
        if root_target:
            return "delete root path"
    return None


def scan_destructive_tokens(command: str) -> Optional[str]:
    """Token-level destructive scan for patterns hard to express as regexes."""
    return _scan_rm_destructive(command)


def _scan_critical_patterns(command: str) -> Optional[str]:
    """Scan command string for deterministic critical patterns.
    Returns reason string if found, None if clean."""
    for regex, reason in CRITICAL_PATTERNS:
        if regex.search(command):
            return reason
    return scan_destructive_tokens(command)


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
