"""
Enhanced shell execution system for HelloChusquis.

Provides:
- ShellTool: Command execution with timeout, PTY, background, streaming, env isolation
- ProcessManager: Process tracking, signals, polling, zombie cleanup, process groups
- CommandQueue: Capacity-limited command queue with priority lanes
- ExecAutoReviewer: Post-execution heuristic code review
- SafeBinPolicy: Binary allowlist, profile-based safety rules

Backward compatible: ShellTool.run(command) and ShellTool.arun(command) still work.
"""

from __future__ import annotations

import asyncio
import fcntl
import logging
import os
import pty
import re
import signal
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

from tools.base import BaseTool, ToolResult
from core.security_evaluator import evaluate_command_safety, scan_destructive_tokens

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_TIMEOUT = 30  # seconds
DEFAULT_MAX_OUTPUT_BYTES = 1024 * 1024  # 1 MB
DEFAULT_QUEUE_CAPACITY = 100
DEFAULT_MAX_CONCURRENT = 4
DEFAULT_KILL_GRACE_MS = 2000
POLL_INTERVAL_MS = 100
DEFAULT_LOG_TAIL_LINES = 200
DEFAULT_MAX_FINISHED_SESSIONS = 100
ZOMBIE_CLEANUP_INTERVAL_S = 30


# ---------------------------------------------------------------------------
# Data classes / enums
# ---------------------------------------------------------------------------

class Priority(IntEnum):
    BACKGROUND = -1
    NORMAL = 0
    FOREGROUND = 1


class ExecRisk(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class ExecDecision(Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


class ProcessStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    KILLED = "killed"


@dataclass
class ExecReviewResult:
    decision: ExecDecision
    risk: ExecRisk
    rationale: str
    suggestions: List[str] = field(default_factory=list)


@dataclass
class ProcessSession:
    id: str
    pid: Optional[int] = None
    command: str = ""
    cwd: str = ""
    started_at: float = 0.0
    ended_at: Optional[float] = None
    status: ProcessStatus = ProcessStatus.RUNNING
    exit_code: Optional[int] = None
    exit_signal: Optional[str] = None
    stdout_buffer: str = ""
    stderr_buffer: str = ""
    aggregated: str = ""
    truncated: bool = False
    backgrounded: bool = False
    pty_master: Optional[int] = None
    pty_slave: Optional[int] = None
    process: Optional[subprocess.Popen] = None

    @property
    def runtime_ms(self) -> float:
        end = self.ended_at or time.time()
        return (end - self.started_at) * 1000

    @property
    def tail(self) -> str:
        lines = self.aggregated.split("\n")
        return "\n".join(lines[-DEFAULT_LOG_TAIL_LINES:])


@dataclass
class QueueEntry:
    id: str
    command: str
    priority: Priority
    enqueued_at: float
    workdir: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    timeout: Optional[int] = None
    task: Optional[Callable] = None
    resolve: Optional[Callable] = None
    reject: Optional[Callable] = None


# ---------------------------------------------------------------------------
# SafeBinPolicy
# ---------------------------------------------------------------------------

# Binaries considered safe to execute without elevated review.
DEFAULT_SAFE_BINS: Set[str] = {
    "ls", "cat", "head", "tail", "wc", "grep", "rg", "find", "which",
    "echo", "printf", "date", "whoami", "hostname", "uname", "pwd",
    "env", "printenv", "true", "false", "test", "basename", "dirname",
    "realpath", "readlink", "stat", "file", "type", "hash",
    "git", "python", "python3", "node", "npm", "npx", "pip", "pip3",
    "cargo", "rustc", "go", "java", "javac",
    "curl", "wget", "ssh", "scp", "rsync",
    "make", "cmake", "gcc", "g++", "clang",
    "docker", "kubectl", "helm",
    "jq", "yq", "xmllint",
    "sort", "uniq", "cut", "tr", "sed", "awk", "xargs",
    "tar", "gzip", "gunzip", "zip", "unzip", "bzip2",
    "tee", "diff", "patch", "chmod", "chown", "mkdir", "touch", "cp", "mv", "rm",
    "ps", "top", "htop", "df", "du", "free", "uptime", "id", "groups",
    "sh", "bash", "zsh", "fish",
}

# Dangerous command patterns — split into catastrophic (DENY) and medium (ASK).
CATASTROPHIC_PATTERNS: List[Tuple[str, str]] = [
    # rm recursive+force — short flags, case variants, clusters with trailing chars
    (r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r)\b", "recursive force delete"),
    (r"\brm\s+-rf\s+/", "root filesystem delete"),
    (r"\brm\s+-fr\s+/", "root filesystem delete"),
    (r"\brm\s+-r\s+-f\s+/", "root filesystem delete"),
    (r"\brm\s+-f\s+-r\s+/", "root filesystem delete"),
    # rm long-form / mixed / cluster flag combos
    (r"\brm\s+--recursive\s+--force\b", "recursive force delete"),
    (r"\brm\s+--force\s+--recursive\b", "recursive force delete"),
    (r"\brm\s+--recursive\s+-[a-zA-Z]*[fF]\b", "recursive force delete"),
    (r"\brm\s+--force\s+-[a-zA-Z]*[rR]\b", "recursive force delete"),
    (r"\brm\s+-[a-zA-Z]*[fF]\s+--recursive\b", "recursive force delete"),
    (r"\brm\s+-[a-zA-Z]*[rR]\s+--force\b", "recursive force delete"),
    (r"\brm\s+-[a-zA-Z]*[rR][a-zA-Z]*[fF]", "recursive force delete"),
    (r"\brm\s+-[a-zA-Z]*[fF][a-zA-Z]*[rR]", "recursive force delete"),
    (r"\brm\s+.*\s+/", "delete root path"),
    (r"\bdd\s+.*of=/dev/", "raw disk write"),
    (r">\s*/dev/sd", "raw disk overwrite"),
    (r">\s*/dev/nvme", "raw disk overwrite"),
    (r":\(\)\s*\{.*\|.*&", "fork bomb"),
    (r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(\)\s*\{[^{}]*\b\1\s*\|\s*\1\b[^{}]*&[^{}]*\}", "fork bomb"),
    (r"\bmkfs\b", "filesystem formatting"),
    (r"\bmke2fs\b", "filesystem formatting"),
    (r"\bnewfs_\w+\b", "filesystem formatting"),
    (r"\bdiskutil\s+(erase\S*|zero\w*|secureErase\S*)\b", "filesystem formatting"),
    (r"\bformat\b.*\b(c:|/dev/)", "filesystem formatting"),
    (r"\bchmod\s+-R\s+777\s+/", "recursive world-writable on root"),
    (r"\bchmod\s+(?:--recursive\s+|-r[a-zA-Z]*\s+)?(0?7777?|[ugoa]*[+-=][rwxXugoa]*)(?:\s+(?:--recursive|-r[a-zA-Z]*))?\s+/(?:\s|$)", "world-writable on root"),
    (r"\bmv\s+/\s+/", "move root filesystem"),
    (r"\bshutdown\b", "system shutdown"),
    (r"\breboot\b", "system reboot"),
    (r"\binit\s+0\b", "init 0 shutdown"),
    (r"^\s*(sudo\s+)?(halt|poweroff)\b", "system shutdown"),
    (r"\bsystemctl\s+(halt|poweroff|reboot)\b", "system shutdown"),
    (r"\bosascript\b.*\b(shut\s?down|restart)\b", "system shutdown via osascript"),
    (r"\btelinit\s+[06]\b", "runlevel shutdown"),
    (r"\b(fdisk|parted|gdisk)\b", "partition manipulation"),
    (r"\bcurl\b.*\|\s*(ba)?sh\b", "remote code execution via pipe"),
    (r"\bwget\b.*\|\s*(ba)?sh\b", "remote code execution via pipe"),
    (r"\bcurl\b.*\|\s*sudo\b", "remote code execution via pipe as root"),
    # Two-stage RCE: download to file, then execute
    (r"\bcurl\b[^;&|\n]*(?:-o|-O|--output|--output-document|--remote-name)[^;&|\n]*(?:&&|;|\n)\s*((ba)?sh|zsh|fish)\b", "download and execute"),
    (r"\bwget\b[^;&|\n]*(?:-O|-o|--output-document)[^;&|\n]*(?:&&|;|\n)\s*((ba)?sh|zsh|fish)\b", "download and execute"),
    # RCE via process substitution: bash <(curl ...)
    (r"\b((ba)?sh|zsh|fish)\s*<\(\s*(curl|wget)\b", "remote code via process substitution"),
    (r"\b(source|\.)\s*<\(\s*(curl|wget)\b", "remote code via process substitution"),
    # RCE via xargs: curl ... | xargs -I{} sh -c {}
    (r"\b(curl|wget)\b.*\|\s*xargs\b.*\b(sh|bash|zsh|fish|python)\b", "remote code via xargs"),
    (r"\b(curl|wget)\b.*\|\s*xargs\b.*\b(rm|dd|mkfs|chmod|mv|shutdown)\b", "remote code via xargs"),
    # sh -c / bash -c with destructive payload
    (r"\b((ba)?sh|zsh|fish)\s+(--command|-c)\b.*\b(rm|dd|mkfs|mke2fs|mv|chmod|chown|shutdown|reboot|halt|poweroff|kill|fdisk|parted|curl|wget)\b", "shell -c with destructive command"),
    # python -c / python3 -c inline code execution
    (r"\bpython3?\s+-c\b.*(?:\bimport\s+(?:os|shutil|subprocess)\b|\bfrom\s+pathlib\b|\bos\.(?:system|remove|rmdir|unlink|popen)\b|\bshutil\.\w+|\brmtree\s*\(|\.unlink\s*\()", "python inline code execution"),
    # find -exec with rm/dd
    (r"\bfind\b.*-exec\s+(rm|dd)\b", "find -exec with destructive command"),
    # find -delete rooted at /, /home, or ~
    (r"\bfind\s+(?:/|/home|~)(?:\s)[^;&|\n]*-delete\b", "recursive delete via find"),
    # kill critical PIDs (init=1, process group=0, everything=-1)
    (r"\bkill\s+-(SIG)?\w+\s+(-?1|0)\b", "kill critical process"),
    (r"\bkill\s+-s\s+(SIG)?\w+\s+(-?1|0)\b", "kill critical process"),
    (r"\bkill\s+-1\b(?=\s*(?:$|[;&|\n]))", "kill all processes"),
    (r"\bkillall\b", "kill all processes"),
    # sudo + destructive commands
    (r"\bsudo\b.*\b(rm\s+-[a-zA-Z]*r[a-zA-Z]*f|dd\s+|mkfs|format|chmod\s+-R\s+777\s+/)\b", "sudo with destructive command"),
]

# Legacy list kept for backward compat with any direct callers
DANGEROUS_PATTERNS: List[Tuple[str, str]] = CATASTROPHIC_PATTERNS + [
    (r"\bchmod\s+777\b", "world-writable permissions"),
    (r"\bchmod\s+-R\s+777\b", "recursive world-writable"),
    (r"\beval\b", "dynamic code evaluation"),
    (r"\bsudo\b", "elevated privileges"),
    (r"\bsu\s+-", "user switching"),
    (r"\bkillall\b", "kill all processes"),
    (r"\bpkill\b.*-9", "force kill all matching"),
    (r"\b(iptables|nft)\b", "firewall modification"),
    (r"\b(systemctl|service)\s+(stop|disable|mask)\b", "service disruption"),
    (r"\bmount\b", "filesystem mounting"),
    (r"\bumount\b", "filesystem unmounting"),
]

# Profile-based safety rules: maps profile name -> config
SAFETY_PROFILES: Dict[str, Dict[str, Any]] = {
    "permissive": {
        "allow_shell": True,
        "allow_network": True,
        "allow_privileged": False,
        "review_level": "low",
    },
    "standard": {
        "allow_shell": True,
        "allow_network": True,
        "allow_privileged": False,
        "review_level": "medium",
    },
    "restricted": {
        "allow_shell": False,
        "allow_network": False,
        "allow_privileged": False,
        "review_level": "high",
    },
    "paranoid": {
        "allow_shell": False,
        "allow_network": False,
        "allow_privileged": False,
        "review_level": "high",
        "max_output_bytes": 1024 * 100,
        "timeout": 10,
    },
}


class SafeBinPolicy:
    """Binary allowlist with profile-based safety rules and dangerous-combo blocking."""

    def __init__(
        self,
        safe_bins: Optional[Set[str]] = None,
        profile: str = "standard",
        extra_allowed: Optional[Set[str]] = None,
        extra_blocked: Optional[Set[str]] = None,
    ):
        self.safe_bins: Set[str] = safe_bins or set(DEFAULT_SAFE_BINS)
        if extra_allowed:
            self.safe_bins.update(extra_allowed)
        if extra_blocked:
            self.safe_bins -= extra_blocked
        self.profile = SAFETY_PROFILES.get(profile, SAFETY_PROFILES["standard"])
        self.profile_name = profile
        self._compiled_catastrophic = [
            (re.compile(pattern, re.IGNORECASE), desc)
            for pattern, desc in CATASTROPHIC_PATTERNS
        ]
        self._compiled_dangerous = [
            (re.compile(pattern, re.IGNORECASE), desc)
            for pattern, desc in DANGEROUS_PATTERNS
        ]

    def is_safe_binary(self, bin_name: str) -> bool:
        base = os.path.basename(bin_name)
        return base in self.safe_bins

    def check_dangerous_patterns(self, command: str) -> List[Tuple[str, str]]:
        violations = []
        seen = set()
        for regex, desc in self._compiled_dangerous:
            if regex.search(command) and desc not in seen:
                violations.append((regex.pattern, desc))
                seen.add(desc)
        return violations

    def _is_catastrophic(self, command: str) -> Optional[str]:
        """Return reason if command matches a catastrophic pattern, else None."""
        # Token-level scan first (rm long-flag / cluster combos).
        token_reason = scan_destructive_tokens(command)
        if token_reason:
            return token_reason
        for regex, desc in self._compiled_catastrophic:
            if regex.search(command):
                return desc
        return None

    @staticmethod
    def _has_tty() -> bool:
        """Check if stdin is a terminal (interactive session)."""
        return hasattr(sys.stdin, "isatty") and sys.stdin.isatty()

    def evaluate(self, command: str, workdir: Optional[str] = None) -> ExecReviewResult:
        """Evaluate command safety.

        Catastrophic patterns → DENY always.
        Medium-risk patterns  → ASK (but ASK becomes DENY if no TTY).
        """
        first_token = command.split()[0] if command.split() else ""

        # Phase 1: catastrophic → hard DENY
        cat_reason = self._is_catastrophic(command)
        if cat_reason:
            return ExecReviewResult(
                decision=ExecDecision.DENY,
                risk=ExecRisk.HIGH,
                rationale=f"Catastrophic: {cat_reason}",
            )

        # Phase 2: dangerous patterns → ASK
        violations = self.check_dangerous_patterns(command)
        if violations:
            risk = ExecRisk.HIGH
            rationale = f"Dangerous patterns: {'; '.join(d for _, d in violations)}"
            decision = ExecDecision.ASK

            # Non-interactive context: ASK → DENY
            if not self._has_tty():
                return ExecReviewResult(
                    decision=ExecDecision.DENY,
                    risk=risk,
                    rationale=f"Blocked (non-interactive): {rationale}",
                    suggestions=["Requires interactive approval"],
                )

            return ExecReviewResult(
                decision=decision,
                risk=risk,
                rationale=rationale,
                suggestions=["Consider using a safer alternative", "Review command intent"],
            )

        # Phase 3: profile-based checks
        if not self.profile.get("allow_shell", True):
            if any(sh in first_token for sh in ["sh", "bash", "zsh"]):
                return ExecReviewResult(
                    decision=ExecDecision.DENY,
                    risk=ExecRisk.MEDIUM,
                    rationale="Shell execution disabled by profile",
                )

        if not self.profile.get("allow_network", True):
            net_bins = {"curl", "wget", "ssh", "scp", "rsync", "nc", "ncat", "telnet"}
            if first_token in net_bins:
                return ExecReviewResult(
                    decision=ExecDecision.DENY,
                    risk=ExecRisk.MEDIUM,
                    rationale="Network access disabled by profile",
                )

        if not self.profile.get("allow_privileged", True):
            priv_bins = {"sudo", "su", "mount", "umount", "fdisk", "parted"}
            if first_token in priv_bins:
                return ExecReviewResult(
                    decision=ExecDecision.DENY,
                    risk=ExecRisk.HIGH,
                    rationale="Privileged execution disabled by profile",
                )

        return ExecReviewResult(
            decision=ExecDecision.ALLOW,
            risk=ExecRisk.LOW,
            rationale="No dangerous patterns detected",
        )


# ---------------------------------------------------------------------------
# ExecAutoReviewer
# ---------------------------------------------------------------------------

class ExecAutoReviewer:
    """Post-execution heuristic code review. Suggests improvements, detects issues."""

    ISSUE_PATTERNS: List[Tuple[str, str, str]] = [
        (r"warning:", "Compiler/linter warning detected", "Review warnings and fix root cause"),
        (r"deprecat(ed|ion)", "Deprecated API or feature used", "Migrate to recommended replacement"),
        (r"error:\s*no such file", "File not found", "Verify path and file existence"),
        (r"permission denied", "Insufficient permissions", "Check file permissions or use elevated mode"),
        (r"port \d+ already in use", "Port conflict", "Kill existing process or use different port"),
        (r"out of memory|oom|oom-killer", "Out of memory", "Reduce memory usage or increase limits"),
        (r"stack overflow", "Stack overflow", "Check for infinite recursion"),
        (r"segmentation fault", "Memory access violation", "Review pointer/array access"),
        (r"connection refused", "Service unreachable", "Verify service is running and port is correct"),
        (r"timeout|timed out", "Operation timed out", "Increase timeout or optimize operation"),
    ]

    IMPROVEMENT_PATTERNS: List[Tuple[str, str, str]] = [
        (r"\bgit add \.", "Unstaged files tracked", "Use 'git add -p' for selective staging"),
        (r"\bkill\b.*\b\d+\b", "Direct PID kill", "Use 'pkill' or 'killall' for named processes"),
        (r"\bcat\b.*\|\s*grep", "Useless use of cat", "Use 'grep FILE' directly"),
        (r"\bfind\b.*-exec\s+rm\b", "find -exec rm", "Use 'find -delete' instead"),
        (r"for\s+\w+\s+in\s+.*;\s+do\s+.*\bcp\b", "Loop with cp", "Use 'cp -r' or rsync"),
        (r"\bhttp://", "Plaintext HTTP", "Prefer HTTPS when available"),
    ]

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._compiled_issues = [
            (re.compile(p, re.IGNORECASE), desc, fix)
            for p, desc, fix in self.ISSUE_PATTERNS
        ]
        self._compiled_improvements = [
            (re.compile(p, re.IGNORECASE), desc, fix)
            for p, desc, fix in self.IMPROVEMENT_PATTERNS
        ]

    def review(
        self,
        command: str,
        stdout: str = "",
        stderr: str = "",
        exit_code: Optional[int] = None,
        workdir: Optional[str] = None,
    ) -> ExecReviewResult:
        if not self.enabled:
            return ExecReviewResult(
                decision=ExecDecision.ALLOW,
                risk=ExecRisk.LOW,
                rationale="Auto-review disabled",
            )

        combined_output = f"{stdout}\n{stderr}"
        issues: List[str] = []
        suggestions: List[str] = []

        for regex, desc, fix in self._compiled_issues:
            if regex.search(combined_output):
                issues.append(desc)
                suggestions.append(fix)

        for regex, desc, fix in self._compiled_improvements:
            if regex.search(command):
                suggestions.append(f"{desc}: {fix}")

        if exit_code and exit_code != 0 and not stderr.strip():
            issues.append(f"Non-zero exit code ({exit_code}) with no stderr")
            suggestions.append("Check command arguments and working directory")

        if issues:
            risk = ExecRisk.MEDIUM if len(issues) <= 2 else ExecRisk.HIGH
            decision = ExecDecision.ASK
            rationale = f"{len(issues)} issue(s) detected: {'; '.join(issues[:3])}"
        elif suggestions:
            risk = ExecRisk.LOW
            decision = ExecDecision.ALLOW
            rationale = f"{len(suggestions)} improvement suggestion(s)"
        else:
            risk = ExecRisk.LOW
            decision = ExecDecision.ALLOW
            rationale = "No issues detected"

        return ExecReviewResult(
            decision=decision,
            risk=risk,
            rationale=rationale,
            suggestions=suggestions,
        )


# ---------------------------------------------------------------------------
# ProcessManager
# ---------------------------------------------------------------------------

class ProcessManager:
    """Track processes with bounded retention for completed sessions."""
    def __init__(
        self,
        kill_grace_ms: int = DEFAULT_KILL_GRACE_MS,
        max_finished_sessions: int = DEFAULT_MAX_FINISHED_SESSIONS,
    ):
        if max_finished_sessions < 1:
            raise ValueError("max_finished_sessions must be at least 1")
        self.kill_grace_ms = kill_grace_ms
        self.max_finished_sessions = max_finished_sessions

        self._sessions: Dict[str, ProcessSession] = {}
        self._finished: Dict[str, ProcessSession] = {}
        self._lock = threading.Lock()
        self._cleanup_thread: Optional[threading.Thread] = None
        self._stop_cleanup = threading.Event()
        self._start_cleanup_thread()

    def _start_cleanup_thread(self) -> None:
        def _cleanup_loop():
            while not self._stop_cleanup.wait(ZOMBIE_CLEANUP_INTERVAL_S):
                self.cleanup_zombies()

        self._cleanup_thread = threading.Thread(target=_cleanup_loop, daemon=True)
        self._cleanup_thread.start()

    def create_session(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        use_pty: bool = False,
        pipe_stdin: bool = False,
    ) -> ProcessSession:
        session_id = f"sess-{uuid.uuid4().hex[:12]}"
        effective_cwd = cwd or os.getcwd()
        effective_env = os.environ.copy()
        if env:
            effective_env.update(env)

        session = ProcessSession(
            id=session_id,
            command=command,
            cwd=effective_cwd,
            started_at=time.time(),
        )

        pty_master_fd = None
        pty_slave_fd = None

        if use_pty:
            try:
                pty_master_fd, pty_slave_fd = pty.openpty()
                session.pty_master = pty_master_fd
                session.pty_slave = pty_slave_fd
            except (OSError, ImportError):
                logger.warning("PTY not available, falling back to pipes")
                use_pty = False

        try:
            if use_pty and pty_slave_fd is not None:
                flags = fcntl.fcntl(pty_master_fd, fcntl.F_GETFL)
                fcntl.fcntl(pty_master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

                proc = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=effective_cwd,
                    env=effective_env,
                    stdin=pty_slave_fd,
                    stdout=pty_slave_fd,
                    stderr=pty_slave_fd,
                    preexec_fn=os.setsid,
                )
                os.close(pty_slave_fd)
                session.pty_slave = None
            else:
                proc = subprocess.Popen(
                    command,
                    shell=True,
                    cwd=effective_cwd,
                    env=effective_env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE if pipe_stdin else subprocess.DEVNULL,
                    preexec_fn=os.setsid,
                )

            session.pid = proc.pid
            session.process = proc
        except Exception:
            session.status = ProcessStatus.FAILED
            session.ended_at = time.time()
            if pty_master_fd is not None:
                try:
                    os.close(pty_master_fd)
                except OSError:
                    pass
            raise

        with self._lock:
            self._sessions[session_id] = session

        return session

    def poll_output(self, session_id: str, timeout_s: float = 0.1) -> Optional[str]:
        with self._lock:
            session = self._sessions.get(session_id)
        if not session or not session.process:
            return None

        new_output = ""

        if session.pty_master is not None:
            try:
                data = os.read(session.pty_master, 65536)
                if data:
                    text = data.decode("utf-8", errors="replace")
                    new_output += text
                    session.stdout_buffer += text
            except OSError:
                pass
        else:
            proc = session.process
            if proc.stdout and hasattr(proc.stdout, "fileno"):
                try:
                    import select
                    fd = proc.stdout.fileno()
                    if select.select([fd], [], [], timeout_s)[0]:
                        chunk = os.read(fd, 65536)
                        if chunk:
                            text = chunk.decode("utf-8", errors="replace")
                            new_output += text
                            session.stdout_buffer += text
                except (BlockingIOError, ValueError, OSError):
                    pass

            if proc.stderr and hasattr(proc.stderr, "fileno"):
                try:
                    import select
                    fd = proc.stderr.fileno()
                    if select.select([fd], [], [], 0)[0]:
                        chunk = os.read(fd, 65536)
                        if chunk:
                            text = chunk.decode("utf-8", errors="replace")
                            new_output += text
                            session.stderr_buffer += text
                except (BlockingIOError, ValueError, OSError):
                    pass

        if new_output:
            session.aggregated += new_output

        if session.process.poll() is not None and not session.ended_at:
            session.ended_at = time.time()
            session.exit_code = session.process.returncode
            session.status = (
                ProcessStatus.COMPLETED
                if session.exit_code == 0
                else ProcessStatus.FAILED
            )
            self._finalize(session_id)

        return new_output if new_output else None

    def poll_until_exit(
        self, session_id: str, timeout: Optional[float] = None
    ) -> ProcessSession:
        start = time.time()
        while True:
            self.poll_output(session_id)
            with self._lock:
                session = self._sessions.get(session_id)
                if not session:
                    break
                if session.ended_at:
                    break
            if timeout and (time.time() - start) >= timeout:
                with self._lock:
                    session = self._sessions.get(session_id)
                    if session and not session.ended_at:
                        session.ended_at = time.time()
                        session.status = ProcessStatus.TIMEOUT
                        session.exit_signal = "SIGTERM"
                self.kill(session_id, reason="timeout")
                break
            time.sleep(POLL_INTERVAL_MS / 1000.0)
        return self.get_session(session_id)

    def get_session(self, session_id: str) -> Optional[ProcessSession]:
        with self._lock:
            return self._sessions.get(session_id) or self._finished.get(session_id)

    def list_running(self) -> List[ProcessSession]:
        with self._lock:
            return [s for s in self._sessions.values() if not s.ended_at]

    def list_finished(self) -> List[ProcessSession]:
        with self._lock:
            return list(self._finished.values())

    def send_signal(self, session_id: str, sig: signal.Signals) -> bool:
        with self._lock:
            session = self._sessions.get(session_id)
        if not session or not session.pid:
            return False
        try:
            os.killpg(os.getpgid(session.pid), sig)
            return True
        except (ProcessLookupError, PermissionError, OSError):
            return False

    def kill(
        self, session_id: str, reason: str = "manual"
    ) -> Optional[ProcessSession]:
        session = self.get_session(session_id)
        if not session or session.ended_at:
            return session

        self.send_signal(session_id, signal.SIGTERM)

        time.sleep(self.kill_grace_ms / 1000.0)
        with self._lock:
            session = self._sessions.get(session_id)
        if session and not session.ended_at:
            self.send_signal(session_id, signal.SIGKILL)
            time.sleep(0.1)

        needs_finalize = False
        with self._lock:
            session = self._sessions.get(session_id)
            if session and not session.ended_at:
                session.ended_at = time.time()
                session.exit_signal = sig_name(reason)
                session.status = ProcessStatus.KILLED
                needs_finalize = True
        if needs_finalize:
            self._finalize(session_id)

        return self.get_session(session_id)

    def _finalize(self, session_id: str) -> None:
        session = None
        with self._lock:
            session = self._sessions.pop(session_id, None)
        if session:
            if session.process and session.process.poll() is None:
                try:
                    session.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
            if session.pty_master is not None:
                try:
                    os.close(session.pty_master)
                except OSError:
                    pass
            session.pty_master = None
            with self._lock:
                self._finished[session_id] = session
                while len(self._finished) > self.max_finished_sessions:
                    self._finished.pop(next(iter(self._finished)))

    def cleanup_zombies(self) -> int:
        cleaned = 0
        with self._lock:
            active_ids = list(self._sessions.keys())

        for sid in active_ids:
            self.poll_output(sid)
            with self._lock:
                session = self._sessions.get(sid)
                if session and session.process and session.ended_at:
                    self._finalize(sid)
                    cleaned += 1
        return cleaned

    def shutdown(self) -> None:
        self._stop_cleanup.set()
        with self._lock:
            active_ids = list(self._sessions.keys())
        for sid in active_ids:
            self.kill(sid, reason="shutdown")


def sig_name(reason: str) -> str:
    mapping = {
        "timeout": "SIGTERM",
        "manual": "SIGTERM",
        "shutdown": "SIGTERM",
        "abort": "SIGKILL",
    }
    return mapping.get(reason, "SIGTERM")


# ---------------------------------------------------------------------------
# CommandQueue
# ---------------------------------------------------------------------------

class CommandQueue:
    """Queue commands with capacity limits, priority lanes, scoped execution, concurrent limits."""

    def __init__(
        self,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        capacity: int = DEFAULT_QUEUE_CAPACITY,
    ):
        self.max_concurrent = max_concurrent
        self.capacity = capacity
        self._lanes: Dict[str, _LaneState] = {}
        self._lock = threading.Lock()
        self._semaphore = threading.Semaphore(max_concurrent)
        self._next_seq = 0
        self._active_count = 0

    def _get_lane(self, lane: str) -> _LaneState:
        if lane not in self._lanes:
            self._lanes[lane] = _LaneState(lane=lane)
        return self._lanes[lane]

    def enqueue(
        self,
        task: Callable[[], Any],
        lane: str = "main",
        priority: Priority = Priority.NORMAL,
        timeout: Optional[int] = None,
        workdir: Optional[str] = None,
        on_wait: Optional[Callable[[float, int], None]] = None,
    ) -> Any:
        with self._lock:
            lane_state = self._get_lane(lane)
            total_depth = sum(
                len(l.queue) + l.active_count for l in self._lanes.values()
            )
            if total_depth > self.capacity:
                raise QueueFullError(f"Queue at capacity ({self.capacity})")

            self._next_seq += 1

        result_container: Dict[str, Any] = {}
        event = threading.Event()

        def _wrapper():
            try:
                result_container["value"] = task()
                result_container["ok"] = True
            except Exception as e:
                result_container["error"] = e
                result_container["ok"] = False
            finally:
                event.set()

        entry = QueueEntry(
            id=f"task-{uuid.uuid4().hex[:8]}",
            command=getattr(task, "__name__", str(task)),
            priority=priority,
            enqueued_at=time.time(),
            workdir=workdir,
            timeout=timeout,
            task=_wrapper,
        )

        with self._lock:
            lane_state.queue.append(entry)
            lane_state.queue.sort(key=lambda e: (-e.priority, e.enqueued_at))

        self._drain_lane(lane)
        event.wait(timeout=timeout)

        if "error" in result_container:
            raise result_container["error"]
        return result_container.get("value")

    async def aenqueue(
        self,
        task: Callable[[], Coroutine],
        lane: str = "main",
        priority: Priority = Priority.NORMAL,
        timeout: Optional[int] = None,
    ) -> Any:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.enqueue(task, lane, priority, timeout),
        )

    def _drain_lane(self, lane: str) -> None:
        with self._lock:
            lane_state = self._get_lane(lane)
            while (
                lane_state.active_count < self.max_concurrent
                and lane_state.queue
            ):
                entry = lane_state.queue.pop(0)
                lane_state.active_count += 1
                self._active_count += 1
                t = threading.Thread(target=self._run_entry, args=(lane, entry), daemon=True)
                t.start()

    def _run_entry(self, lane: str, entry: QueueEntry) -> None:
        try:
            if entry.task:
                entry.task()
        finally:
            with self._lock:
                lane_state = self._get_lane(lane)
                lane_state.active_count = max(0, lane_state.active_count - 1)
                self._active_count = max(0, self._active_count - 1)
            self._drain_lane(lane)

    def snapshot(self, lane: str = "main") -> Dict[str, Any]:
        with self._lock:
            lane_state = self._get_lane(lane)
            return {
                "lane": lane,
                "queued_count": len(lane_state.queue),
                "active_count": lane_state.active_count,
                "max_concurrent": self.max_concurrent,
                "total_active": self._active_count,
            }

    def clear_lane(self, lane: str = "main") -> int:
        with self._lock:
            lane_state = self._get_lane(lane)
            count = len(lane_state.queue)
            lane_state.queue.clear()
            return count

    def clear_all(self) -> int:
        total = 0
        with self._lock:
            for lane_state in self._lanes.values():
                total += len(lane_state.queue)
                lane_state.queue.clear()
        return total


@dataclass
class _LaneState:
    lane: str = "main"
    queue: List[QueueEntry] = field(default_factory=list)
    active_count: int = 0


class QueueFullError(Exception):
    pass


# ---------------------------------------------------------------------------
# ShellTool (enhanced, backward compatible)
# ---------------------------------------------------------------------------

class ShellTool(BaseTool):
    """
    Enhanced shell execution tool for HelloChusquis.

    Backward compatible: run(command) and arun(command) still work.
    New features: PTY, background, streaming, env isolation, process tracking,
    command queue, auto-review, safe-bin policy, security evaluator gate.
    """

    name = "shell"
    description = "Ejecuta comandos en la terminal del sistema"

    def __init__(
        self,
        *,
        default_timeout: int = DEFAULT_TIMEOUT,
        max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
        profile: str = "standard",
        allow_background: bool = True,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT,
        queue_capacity: int = DEFAULT_QUEUE_CAPACITY,
        auto_review: bool = True,
        kill_grace_ms: int = DEFAULT_KILL_GRACE_MS,
        **kwargs: Any,
    ):
        self.default_timeout = default_timeout
        self.max_output_bytes = max_output_bytes
        self.allow_background = allow_background
        self.auto_review_enabled = auto_review
        self.process_manager = ProcessManager(kill_grace_ms=kill_grace_ms)
        self.command_queue = CommandQueue(
            max_concurrent=max_concurrent,
            capacity=queue_capacity,
        )
        self.safe_policy = SafeBinPolicy(profile=profile)
        self.auto_reviewer = ExecAutoReviewer(enabled=auto_review)
        self._sessions: Dict[str, ProcessSession] = {}

    # ------------------------------------------------------------------
    # Safety gate (shared between foreground and background)
    # ------------------------------------------------------------------

    @staticmethod
    def _is_unsafe_mode() -> bool:
        """Check if user explicitly opted out of safety checks."""
        return os.getenv("HELLOCHUSQUIS_UNSAFE_MODE") == "1"

    def _safety_gate(self, command: str) -> Optional[ToolResult]:
        """Run all safety checks before execution.

        Returns ToolResult with error if blocked, None if safe to proceed.
        """
        # Unsafe mode escape hatch
        if self._is_unsafe_mode():
            return None

        # 1. Security evaluator (deterministic critical patterns + LLM fallback)
        safety = evaluate_command_safety(command, pool=None)
        if not safety.get("safe", True):
            return ToolResult(
                success=False,
                output="",
                error=f"Blocked: {safety.get('reason', 'unsafe command')}",
            )

        # 2. Safe-bin policy (catastrophic → DENY, medium → ASK/DENY)
        policy_result = self.safe_policy.evaluate(command)
        if policy_result.decision == ExecDecision.DENY:
            return ToolResult(
                success=False,
                output="",
                error=f"Blocked by policy: {policy_result.rationale}",
            )

        return None

    # ------------------------------------------------------------------
    # Backward-compatible interface
    # ------------------------------------------------------------------

    def run(self, action: str = "list", **kwargs) -> ToolResult:
        """
        Backward-compatible entry point.

        Legacy usage:  tool.run(command="ls -la")
        New usage:     tool.run(action="exec", command="ls -la", pty=True)
        """
        command = kwargs.pop("command", None)

        # Backward compat: if command kwarg present, treat as exec
        if command and action == "list":
            return self._exec_foreground(command, **kwargs)

        if action == "list":
            return self._list_sessions()

        session_id = kwargs.pop("session_id", "")
        data = kwargs.pop("data", "")
        offset = kwargs.pop("offset", 0)
        limit = kwargs.pop("limit", DEFAULT_LOG_TAIL_LINES)

        action_map = {
            "exec": lambda: self._exec_foreground(command or "", **kwargs),
            "background": lambda: self._exec_background(command or "", **kwargs),
            "poll": lambda: self._poll(session_id, **kwargs),
            "log": lambda: self._log(session_id, offset=offset, limit=limit, **kwargs),
            "kill": lambda: self._kill(session_id),
            "clear": lambda: self._clear(session_id),
            "remove": lambda: self._remove(session_id),
            "write": lambda: self._write(session_id, data),
            "submit": lambda: self._submit(session_id),
        }

        handler = action_map.get(action)
        if handler:
            return handler()
        return ToolResult(success=False, output="", error=f"Unknown action: {action}")

    async def arun(self, command: str, **kwargs) -> ToolResult:
        """Async version — backward compatible."""
        return await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._exec_foreground(command, **kwargs)
        )

    # ------------------------------------------------------------------
    # Exec flow
    # ------------------------------------------------------------------

    def _exec_foreground(
        self,
        command: str,
        *,
        timeout: Optional[int] = None,
        workdir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        use_pty: bool = False,
        background: bool = False,
        **_kwargs: Any,
    ) -> ToolResult:
        if not command.strip():
            return ToolResult(success=False, output="", error="No command provided")

        effective_timeout = timeout or self.default_timeout

        # Safety gate — blocks before execution
        blocked = self._safety_gate(command)
        if blocked is not None:
            return blocked

        # Execute through process manager
        try:
            session = self.process_manager.create_session(
                command=command,
                cwd=workdir,
                env=env,
                use_pty=use_pty,
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to start process: {e}")

        self._sessions[session.id] = session

        if background or (not self.allow_background and False):
            session.backgrounded = True
            return ToolResult(
                success=True,
                output=(
                    f"Command running in background (session {session.id}, "
                    f"pid {session.pid}). Use process poll/log/kill for follow-up."
                ),
            )

        # Foreground: wait for completion
        session = self.process_manager.poll_until_exit(session.id, timeout=effective_timeout)

        if session.status == ProcessStatus.TIMEOUT:
            return ToolResult(
                success=False,
                output=session.stdout_buffer,
                error=f"Command timed out after {effective_timeout}s",
            )

        stdout = session.stdout_buffer
        stderr = session.stderr_buffer

        # Auto-review
        review = None
        if self.auto_review_enabled:
            review = self.auto_reviewer.review(
                command=command,
                stdout=stdout,
                stderr=stderr,
                exit_code=session.exit_code,
                workdir=workdir,
            )

        if session.status == ProcessStatus.KILLED:
            return ToolResult(
                success=False,
                output=stdout,
                error=f"Process killed: {stderr}" if stderr else "Process killed",
            )

        if session.exit_code == 0:
            output = stdout
            if review and review.suggestions:
                output += f"\n\n[Suggestions] {'; '.join(review.suggestions)}"
            return ToolResult(success=True, output=output)

        return ToolResult(success=False, output=stdout, error=stderr)

    def _exec_background(
        self, command: str, *, workdir: Optional[str] = None, env: Optional[Dict[str, str]] = None,
        use_pty: bool = False, **_kwargs: Any,
    ) -> ToolResult:
        if not command.strip():
            return ToolResult(success=False, output="", error="No command provided")

        # Safety gate — blocks before execution
        blocked = self._safety_gate(command)
        if blocked is not None:
            return blocked

        try:
            session = self.process_manager.create_session(
                command=command,
                cwd=workdir,
                env=env,
                use_pty=use_pty,
                pipe_stdin=True,
            )
            session.backgrounded = True
            self._sessions[session.id] = session
            return ToolResult(
                success=True,
                output=(
                    f"Command started in background (session {session.id}, "
                    f"pid {session.pid}). Use process poll/log/kill for follow-up."
                ),
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Failed to start: {e}")

    # ------------------------------------------------------------------
    # Process management actions
    # ------------------------------------------------------------------

    def _list_sessions(self) -> ToolResult:
        running = self.process_manager.list_running()
        finished = self.process_manager.list_finished()

        lines = []
        for s in sorted(running, key=lambda x: x.started_at, reverse=True):
            lines.append(
                f"{s.id}  running   {s.runtime_ms:.0f}ms  :: {s.command[:80]}"
            )
        for s in sorted(finished, key=lambda x: x.started_at, reverse=True)[:20]:
            lines.append(
                f"{s.id}  {s.status.value:9s} {s.runtime_ms:.0f}ms  :: {s.command[:80]}"
            )

        text = "\n".join(lines) if lines else "No running or recent sessions."
        return ToolResult(success=True, output=text)

    def _poll(self, session_id: str, **kwargs) -> ToolResult:
        if not session_id:
            return ToolResult(success=False, output="", error="session_id required")

        session = self.process_manager.get_session(session_id)
        if not session:
            return ToolResult(success=False, output="", error=f"No session: {session_id}")

        if not session.ended_at:
            self.process_manager.poll_output(session_id)

        session = self.process_manager.get_session(session_id)
        if not session:
            return ToolResult(success=False, output="", error=f"Session disappeared: {session_id}")

        output = session.stdout_buffer.strip() or session.stderr_buffer.strip() or "(no new output)"
        if session.ended_at:
            exit_info = (
                f"signal {session.exit_signal}"
                if session.exit_signal
                else f"code {session.exit_code}"
            )
            output += f"\n\nProcess exited with {exit_info}."
        else:
            output += "\n\nProcess still running."

        return ToolResult(
            success=True,
            output=output,
            error="" if session.exit_code == 0 else output,
        )

    def _log(self, session_id: str, offset: int = 0, limit: int = DEFAULT_LOG_TAIL_LINES, **_kw) -> ToolResult:
        if not session_id:
            return ToolResult(success=False, output="", error="session_id required")

        session = self.process_manager.get_session(session_id)
        if not session:
            return ToolResult(success=False, output="", error=f"No session: {session_id}")

        if not session.ended_at:
            self.process_manager.poll_output(session_id)
            session = self.process_manager.get_session(session_id) or session

        lines = session.aggregated.split("\n")
        total = len(lines)
        sliced = lines[offset:offset + limit] if limit else lines[offset:]
        text = "\n".join(sliced) or "(no output yet)"
        if offset == 0 and limit == DEFAULT_LOG_TAIL_LINES and total > limit:
            text += f"\n\n[showing last {limit} of {total} lines; pass offset/limit to page]"

        return ToolResult(success=True, output=text)

    def _kill(self, session_id: str, **_kw) -> ToolResult:
        if not session_id:
            return ToolResult(success=False, output="", error="session_id required")

        session = self.process_manager.kill(session_id)
        if not session:
            return ToolResult(success=False, output="", error=f"No active session: {session_id}")

        return ToolResult(success=True, output=f"Killed session {session_id}.")

    def _clear(self, session_id: str) -> ToolResult:
        if not session_id:
            return ToolResult(success=False, output="", error="session_id required")

        with self.process_manager._lock:
            removed = self.process_manager._finished.pop(session_id, None)
        if removed:
            return ToolResult(success=True, output=f"Cleared session {session_id}.")
        return ToolResult(success=False, output="", error=f"No finished session: {session_id}")

    def _remove(self, session_id: str) -> ToolResult:
        if not session_id:
            return ToolResult(success=False, output="", error="session_id required")

        session = self.process_manager.get_session(session_id)
        if not session:
            return ToolResult(success=False, output="", error=f"No session: {session_id}")

        if not session.ended_at:
            self.process_manager.kill(session_id)

        with self.process_manager._lock:
            self.process_manager._finished.pop(session_id, None)
            self.process_manager._sessions.pop(session_id, None)
        self._sessions.pop(session_id, None)

        return ToolResult(success=True, output=f"Removed session {session_id}.")

    def _write(self, session_id: str, data: str) -> ToolResult:
        if not session_id:
            return ToolResult(success=False, output="", error="session_id required")

        session = self.process_manager.get_session(session_id)
        if not session or not session.process or not session.process.stdin:
            return ToolResult(success=False, output="", error=f"Cannot write to session {session_id}")

        try:
            session.process.stdin.write(data.encode("utf-8"))
            session.process.stdin.flush()
            return ToolResult(success=True, output=f"Wrote {len(data)} bytes to {session_id}.")
        except (BrokenPipeError, OSError) as e:
            return ToolResult(success=False, output="", error=f"Write failed: {e}")

    def _submit(self, session_id: str) -> ToolResult:
        return self._write(session_id, "\r")

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def shutdown(self) -> None:
        self.process_manager.shutdown()
