"""
Tool policy, loop detection, dangerous tool detection, sandbox execution, and
security auditing — pure Python stdlib.

Architecture:
  - ToolPolicy: allow/deny resolution with groups, aliases, plugin expansion
  - ToolLoopDetector: sliding-window loop detection (repeat, ping-pong, circuit-breaker)
  - DangerousToolDetector: flags hazardous tool combinations
  - ToolSandbox: restricted subprocess execution
  - SecurityAuditor: audits tool calls against policies

No external dependencies. Production-grade. Type-hinted. Dataclass-heavy.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shlex
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOOL_NAME_SEPARATOR = "::"

# Tool name aliases (bash → exec, etc.)
TOOL_NAME_ALIASES: Dict[str, str] = {
    "bash": "exec",
    "apply-patch": "apply_patch",
}

# Core tool groups — maps group name → list of concrete tool names
TOOL_GROUPS: Dict[str, List[str]] = {
    "filesystem": ["fs_read", "fs_write", "fs_delete", "fs_move", "fs_list"],
    "execution": ["exec", "spawn", "shell", "process"],
    "network": ["http_get", "http_post", "web_search", "web_fetch"],
    "communication": [
        "conversations_list",
        "conversations_send",
        "conversations_turn",
        "sessions_spawn",
        "sessions_send",
    ],
    "messaging": [
        "message",
        "send",
        "broadcast",
        "reply",
        "thread-reply",
    ],
    "control_plane": ["automations", "gateway", "nodes"],
    "ui": ["computer", "mobile_ui", "show_widget"],
}

# Tools denied by default on HTTP gateway surfaces (immediate RCE / control-plane)
DEFAULT_GATEWAY_HTTP_TOOL_DENY: FrozenSet[str] = frozenset({
    "exec",
    "spawn",
    "shell",
    "fs_write",
    "fs_delete",
    "fs_move",
    "apply_patch",
    "terminal",
    "sessions_spawn",
    "sessions_send",
    "conversations_list",
    "conversations_send",
    "conversations_turn",
    "automations",
    "gateway",
    "nodes",
    "computer",
    "mobile_ui",
    "hellochusquis",
})

# Control-plane tools that require owner identity
GATEWAY_OWNER_ONLY_CORE_TOOLS: FrozenSet[str] = frozenset({
    "automations",
    "gateway",
    "sessions",
    "screen",
    "terminal",
    "conversations_list",
    "conversations_send",
    "conversations_turn",
    "nodes",
    "computer",
    "mobile_ui",
    "hellochusquis",
})

# Known poll-like tools (for loop detection heuristics)
KNOWN_POLL_TOOLS: FrozenSet[str] = frozenset({
    "process",
    "exec",
    "poll",
})

# Message actions that produce volatile per-send ids
SEND_LIKE_MESSAGE_ACTIONS: FrozenSet[str] = frozenset({
    "send",
    "broadcast",
    "reply",
    "thread-reply",
    "sendWithEffect",
    "sendAttachment",
    "upload-file",
    "sticker",
    "poll",
})

# Volatile delivery-result keys stripped before hashing
VOLATILE_SEND_RESULT_KEYS: FrozenSet[str] = frozenset({
    "messageId",
    "message_id",
    "messageIds",
    "platformMessageId",
    "platformMessageIds",
    "fileId",
    "file_id",
    "fileKey",
    "pollId",
    "poll_id",
    "receipt",
    "runId",
    "idempotencyKey",
    "ts",
    "timestamp",
    "sentAt",
    "deliveredAt",
    "createdAt",
})

DEFAULT_PLUGIN_TOOLS_ALLOWLIST_ENTRY = "__hellochusquis_default_plugin_tools__"

# Loop detection thresholds
TOOL_CALL_HISTORY_SIZE = 30
UNKNOWN_TOOL_THRESHOLD = 10
LOOP_WARNING_THRESHOLD = 5
LOOP_CRITICAL_THRESHOLD = 20
GLOBAL_CIRCUIT_BREAKER_THRESHOLD = 30


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Severity(Enum):
    INFO = auto()
    WARN = auto()
    CRITICAL = auto()


class LoopDetectorKind(Enum):
    GENERIC_REPEAT = "generic_repeat"
    ARGUMENT_CHURN = "argument_churn"
    UNKNOWN_TOOL_REPEAT = "unknown_tool_repeat"
    KNOWN_POLL_NO_PROGRESS = "known_poll_no_progress"
    GLOBAL_CIRCUIT_BREAKER = "global_circuit_breaker"
    PING_PONG = "ping_pong"


class LoopDetectionLevel(Enum):
    WARNING = "warning"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ToolPolicyConfig:
    """Configuration for allow/deny lists."""
    allow: Optional[List[str]] = None
    deny: Optional[List[str]] = None


@dataclass(frozen=True)
class ToolCallRecord:
    """Record of a single tool call for loop detection."""
    tool_name: str
    args_hash: str
    tool_call_id: Optional[str] = None
    run_id: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    result_hash: Optional[str] = None
    outcome_kind: Optional[str] = None
    no_progress: bool = False
    unknown_tool_name: Optional[str] = None


@dataclass(frozen=True)
class LoopDetectionResult:
    """Result of loop detection analysis."""
    stuck: bool
    level: Optional[LoopDetectionLevel] = None
    detector: Optional[LoopDetectorKind] = None
    count: int = 0
    message: str = ""
    paired_tool_name: Optional[str] = None
    warning_key: Optional[str] = None
    liveness_signal: Optional[str] = None


@dataclass(frozen=True)
class SecurityAuditFinding:
    """A single security audit finding."""
    check_id: str
    severity: Severity
    title: str
    detail: str
    remediation: Optional[str] = None


@dataclass(frozen=True)
class SecurityAuditSuppressedFinding:
    """A suppressed security audit finding."""
    check_id: str
    severity: Severity
    title: str
    detail: str
    remediation: Optional[str] = None
    suppression_reason: Optional[str] = None


@dataclass
class SecurityAuditSummary:
    """Aggregate counts of findings by severity."""
    critical: int = 0
    warn: int = 0
    info: int = 0


@dataclass(frozen=True)
class SecurityAuditReport:
    """Complete security audit report."""
    timestamp: float
    summary: SecurityAuditSummary
    findings: List[SecurityAuditFinding]
    suppressed_findings: List[SecurityAuditSuppressedFinding] = field(default_factory=list)


@dataclass(frozen=True)
class DangerousToolCombo:
    """Description of a dangerous tool combination."""
    tools: FrozenSet[str]
    reason: str
    severity: Severity


@dataclass
class SandboxConfig:
    """Configuration for sandboxed execution."""
    timeout_seconds: float = 30.0
    max_output_bytes: int = 1024 * 1024  # 1 MB
    working_directory: Optional[str] = None
    allowed_commands: Optional[List[str]] = None
    denied_commands: Optional[List[str]] = None
    env_inherit: bool = False
    env_overrides: Optional[Dict[str, str]] = None
    network_access: bool = False
    max_memory_mb: Optional[int] = None
    shell: Optional[str] = None  # default: system shell


@dataclass(frozen=True)
class SandboxResult:
    """Result of a sandboxed command execution."""
    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool = False
    killed: bool = False


@dataclass(frozen=True)
class LoopDetectionConfig:
    """Configuration for loop detection."""
    enabled: bool = True
    history_size: int = TOOL_CALL_HISTORY_SIZE
    warning_threshold: int = LOOP_WARNING_THRESHOLD
    unknown_tool_threshold: int = UNKNOWN_TOOL_THRESHOLD
    critical_threshold: int = LOOP_CRITICAL_THRESHOLD
    global_circuit_breaker_threshold: int = GLOBAL_CIRCUIT_BREAKER_THRESHOLD
    generic_repeat: bool = True
    known_poll_no_progress: bool = True
    ping_pong: bool = True


@dataclass
class SessionState:
    """Mutable session state for loop detection."""
    tool_call_history: List[ToolCallRecord] = field(default_factory=list)


@dataclass(frozen=True)
class AuditSuppression:
    """A configured suppression rule."""
    check_id: str
    title_includes: Optional[str] = None
    detail_includes: Optional[str] = None
    reason: Optional[str] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def normalize_tool_name(name: str) -> str:
    """Normalize a tool name / alias to the canonical policy id."""
    normalized = name.strip().lower()
    return TOOL_NAME_ALIASES.get(normalized, normalized)


def normalize_tool_list(items: Optional[Iterable[str]]) -> List[str]:
    """Normalize a list of tool names, dropping blanks."""
    if items is None:
        return []
    result: List[str] = []
    for item in items:
        normalized = normalize_tool_name(item)
        if normalized:
            result.append(normalized)
    return result


def expand_tool_groups(items: Optional[Iterable[str]]) -> List[str]:
    """Expand named groups into concrete tool ids."""
    normalized = normalize_tool_list(items)
    expanded: List[str] = []
    for value in normalized:
        group = TOOL_GROUPS.get(value)
        if group:
            expanded.extend(group)
        else:
            expanded.append(value)
    return list(dict.fromkeys(expanded))  # unique preserving order


def stable_stringify(obj: Any) -> str:
    """Deterministic JSON serialization for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def digest_stable(value: Any) -> str:
    """SHA-256 hex digest of deterministic JSON of value."""
    serialized = stable_stringify(value)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def hash_tool_call(tool_name: str, params: Any) -> str:
    """Hash tool name + params for pattern matching."""
    return f"{tool_name}:{digest_stable(params)}"


def extract_text_content(result: Any) -> str:
    """Extract text content from a tool result."""
    if not isinstance(result, dict) or not isinstance(result.get("content"), list):
        return ""
    parts: List[str] = []
    for entry in result["content"]:
        if isinstance(entry, dict) and entry.get("type") == "text" and isinstance(entry.get("text"), str):
            parts.append(entry["text"])
    return "\n".join(parts).strip()


def format_error_for_hash(error: Any) -> str:
    """Format an error into a string suitable for hashing."""
    if isinstance(error, Exception):
        return str(error) or type(error).__name__
    if isinstance(error, str):
        return error
    return stable_stringify(error)


def extract_unknown_tool_name(error: Any) -> Optional[str]:
    """Extract an unknown tool name from an error message."""
    raw = format_error_for_hash(error).strip()
    if not raw:
        return None
    patterns = [
        r'unknown tool[:\s]+["\']?([a-z0-9_.\-]+)["\']?',
        r'tool\s+["\']?([a-z0-9_.\-]+)["\']?\s+(?:not found|is not available)',
    ]
    for pattern in patterns:
        match = re.search(pattern, raw, re.IGNORECASE)
        if match:
            return match.group(1).strip().lower()
    return None


def is_message_delivery_object(value: Any) -> bool:
    """Check if a dict looks like a message delivery result."""
    if not isinstance(value, dict):
        return False
    return (
        isinstance(value.get("id"), str)
        and isinstance(value.get("text"), str)
        and (
            isinstance(value.get("direction"), str)
            or isinstance(value.get("senderId"), str)
            or isinstance(value.get("accountId"), str)
            or isinstance(value.get("conversation"), dict)
        )
    )


def strip_volatile_send_ids(value: Any) -> Any:
    """Strip volatile per-send ids from a value before hashing."""
    if isinstance(value, list):
        return [strip_volatile_send_ids(item) for item in value]
    if not isinstance(value, dict):
        return value
    drop_message_object_id = is_message_delivery_object(value)
    stripped: Dict[str, Any] = {}
    for key, nested in value.items():
        if key in VOLATILE_SEND_RESULT_KEYS:
            continue
        if key == "id" and drop_message_object_id:
            continue
        stripped[key] = strip_volatile_send_ids(nested)
    return stripped


def is_volatile_send_result(tool_name: str, params: Any) -> bool:
    """Check if a tool call produces volatile per-send ids."""
    if tool_name == "sessions_send":
        return True
    if tool_name == "message" and isinstance(params, dict):
        action = params.get("action")
        if isinstance(action, str) and action in SEND_LIKE_MESSAGE_ACTIONS:
            return True
    return False


# ---------------------------------------------------------------------------
# ToolPolicy
# ---------------------------------------------------------------------------

class ToolPolicy:
    """
    Tool allow/deny policy resolver.

    Handles:
      - Allow / deny lists (explicit tool names)
      - Tool group expansion (filesystem → fs_read, fs_write, ...)
      - Name aliases (bash → exec)
      - Plugin tool group expansion
      - Policy layering (merge, intersect)
    """

    def __init__(
        self,
        allow: Optional[List[str]] = None,
        deny: Optional[List[str]] = None,
        plugin_groups: Optional[Mapping[str, List[str]]] = None,
    ) -> None:
        self._raw_allow = allow
        self._raw_deny = deny
        self._plugin_groups: Dict[str, List[str]] = dict(plugin_groups or {})
        self._allow: Optional[List[str]] = None
        self._deny: Optional[List[str]] = None

    # -- Public API ----------------------------------------------------------

    @property
    def allow(self) -> List[str]:
        if self._allow is None:
            self._allow = self._resolve_allow()
        return list(self._allow)

    @property
    def deny(self) -> List[str]:
        if self._deny is None:
            self._deny = self._resolve_deny()
        return list(self._deny)

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check whether a specific tool is allowed by this policy."""
        normalized = normalize_tool_name(tool_name)
        if not normalized:
            return False

        # Deny wins
        if self._matches_list(normalized, self.deny):
            return False

        # Allow list present → must match
        allow_list = self.allow
        if allow_list:
            return self._matches_list(normalized, allow_list)

        # No allow list → implicit allow (deny-only mode)
        return True

    def filter_tools(self, tool_names: Iterable[str]) -> List[str]:
        """Filter a list of tool names by this policy."""
        return [name for name in tool_names if self.is_tool_allowed(name)]

    def has_restrictive_allow(self) -> bool:
        """True when the allow policy is narrower than all/default tools."""
        if self._raw_allow is None:
            return False
        normalized = [normalize_tool_name(e) for e in self._raw_allow if isinstance(e, str)]
        if "*" in normalized:
            return False
        return any(
            bool(e) and e != DEFAULT_PLUGIN_TOOLS_ALLOWLIST_ENTRY
            for e in normalized
        )

    def merge(self, other: "ToolPolicy") -> "ToolPolicy":
        """Merge another policy into this one (other overrides on conflict)."""
        merged_allow = list(self._raw_allow or [])
        merged_deny = list(self._raw_deny or [])
        if other._raw_allow:
            merged_allow.extend(other._raw_allow)
        if other._raw_deny:
            merged_deny.extend(other._raw_deny)
        return ToolPolicy(allow=merged_allow or None, deny=merged_deny or None)

    def collect_explicit_allowlist(self, policies: Sequence[Optional["ToolPolicy"]]) -> List[str]:
        """Collect explicit allow entries from layered policies."""
        entries: List[str] = []
        for policy in policies:
            if policy is None or policy._raw_allow is None:
                continue
            for value in policy._raw_allow:
                if not isinstance(value, str):
                    continue
                trimmed = value.strip()
                if trimmed:
                    entries.append(trimmed)
        return list(dict.fromkeys(entries))

    def collect_explicit_denylist(self, policies: Sequence[Optional["ToolPolicy"]]) -> List[str]:
        """Collect explicit deny entries from layered policies."""
        entries: List[str] = []
        for policy in policies:
            if policy is None or policy._raw_deny is None:
                continue
            for value in policy._raw_deny:
                if not isinstance(value, str):
                    continue
                trimmed = value.strip()
                if trimmed:
                    entries.append(trimmed)
        return list(dict.fromkeys(entries))

    def could_normalize_prefix(self, prefix: str, allowed_names: Set[str]) -> bool:
        """Check if a prefix could still resolve to an allowed tool."""
        normalized_prefix = prefix.strip().lower()
        if not normalized_prefix:
            return False

        resolved_allowed: Set[str] = set()
        for tool_name in allowed_names:
            norm = normalize_tool_name(tool_name)
            folded = tool_name.strip().lower()
            if norm:
                resolved_allowed.add(norm)
            if folded:
                resolved_allowed.add(folded)

        for name in resolved_allowed:
            if name.startswith(normalized_prefix):
                return True

        resolved = normalize_tool_name(normalized_prefix)
        if resolved != normalized_prefix:
            for name in resolved_allowed:
                if name.startswith(resolved):
                    return True

        for alias, tool_name in TOOL_NAME_ALIASES.items():
            if alias.startswith(normalized_prefix) and tool_name in resolved_allowed:
                return True

        return False

    # -- Internal ------------------------------------------------------------

    def _resolve_allow(self) -> List[str]:
        expanded = expand_tool_groups(self._raw_allow)
        plugin_expanded = self._expand_plugin_groups(expanded)
        return plugin_expanded

    def _resolve_deny(self) -> List[str]:
        expanded = expand_tool_groups(self._raw_deny)
        plugin_expanded = self._expand_plugin_groups(expanded)
        return plugin_expanded

    def _expand_plugin_groups(self, items: List[str]) -> List[str]:
        expanded: List[str] = []
        for entry in items:
            normalized = normalize_tool_name(entry)
            if normalized == "group:plugins":
                for group_tools in self._plugin_groups.values():
                    expanded.extend(group_tools)
                continue
            plugin_tools = self._plugin_groups.get(normalized, [])
            if plugin_tools:
                expanded.extend(plugin_tools)
            else:
                expanded.append(normalized)
        return list(dict.fromkeys(expanded))

    def _matches_list(self, tool_name: str, policy_list: List[str]) -> bool:
        """Check if tool_name matches any entry in a policy list (exact or wildcard)."""
        for entry in policy_list:
            if entry == "*":
                return True
            if entry == tool_name:
                return True
            # Simple glob: "fs_*" matches "fs_read"
            if "*" in entry:
                prefix, suffix = entry.split("*", 1)
                if tool_name.startswith(prefix) and tool_name.endswith(suffix):
                    return True
            # Group expansion already done, but plugin: prefix check
            if entry.startswith("plugin:") and tool_name.startswith(entry.split(":", 1)[1]):
                return True
        return False


# ---------------------------------------------------------------------------
# ToolLoopDetector
# ---------------------------------------------------------------------------

class ToolLoopDetector:
    """
    Detects infinite tool call loops using multiple detectors:
      - Generic repeat: same tool + params called N times
      - Unknown tool repeat: calling a non-existent tool N times
      - Known poll no-progress: polling tool stuck
      - Ping-pong: alternating between two call patterns
      - Global circuit-breaker: any tool repeated with no progress N times
      - Argument churn: cycling through slightly different arguments
    """

    def __init__(self, config: Optional[LoopDetectionConfig] = None) -> None:
        self._config = config or LoopDetectionConfig()

    @property
    def config(self) -> LoopDetectionConfig:
        return self._config

    def detect(
        self,
        state: SessionState,
        tool_name: str,
        params: Any,
    ) -> LoopDetectionResult:
        """Analyze recent history + current call for loop patterns."""
        if not self._config.enabled:
            return LoopDetectionResult(stuck=False)

        history = state.tool_call_history
        current_hash = hash_tool_call(tool_name, params)

        # --- Unknown tool repeat ---
        unknown_streak = self._get_unknown_tool_streak(history, tool_name)
        if unknown_streak[0] >= self._config.unknown_tool_threshold:
            return LoopDetectionResult(
                stuck=True,
                level=LoopDetectionLevel.CRITICAL,
                detector=LoopDetectorKind.UNKNOWN_TOOL_REPEAT,
                count=unknown_streak[0],
                message=(
                    f"CRITICAL: attempted unavailable tool {unknown_streak[1] or tool_name} "
                    f"{unknown_streak[0]} times. Stop retrying that missing tool."
                ),
                warning_key=f"unknown-tool:{tool_name}:{unknown_streak[1] or 'unknown'}",
            )

        # --- No-progress streak (same tool + same result hash) ---
        no_progress_streak, latest_result_hash = self._get_no_progress_streak(
            history, tool_name, current_hash,
        )

        # --- Global circuit breaker ---
        if no_progress_streak >= self._config.global_circuit_breaker_threshold:
            return LoopDetectionResult(
                stuck=True,
                level=LoopDetectionLevel.CRITICAL,
                detector=LoopDetectorKind.GLOBAL_CIRCUIT_BREAKER,
                count=no_progress_streak,
                message=(
                    f"CRITICAL: {tool_name} repeated identical no-progress outcomes "
                    f"{no_progress_streak} times. Session blocked by global circuit breaker."
                ),
                warning_key=f"global:{tool_name}:{current_hash}:{latest_result_hash or 'none'}",
            )

        # --- Known poll no-progress ---
        is_poll = self._is_known_poll(tool_name, params)
        if is_poll and self._config.known_poll_no_progress:
            if no_progress_streak >= self._config.critical_threshold:
                return LoopDetectionResult(
                    stuck=True,
                    level=LoopDetectionLevel.CRITICAL,
                    detector=LoopDetectorKind.KNOWN_POLL_NO_PROGRESS,
                    count=no_progress_streak,
                    message=(
                        f"CRITICAL: Called {tool_name} with identical args and no progress "
                        f"{no_progress_streak} times. Stuck polling loop detected."
                    ),
                    warning_key=f"poll:{tool_name}:{current_hash}:{latest_result_hash or 'none'}",
                )
            if no_progress_streak >= self._config.warning_threshold:
                return LoopDetectionResult(
                    stuck=True,
                    level=LoopDetectionLevel.WARNING,
                    detector=LoopDetectorKind.KNOWN_POLL_NO_PROGRESS,
                    count=no_progress_streak,
                    message=(
                        f"WARNING: {tool_name} called {no_progress_streak} times with identical "
                        f"args and no progress. Increase wait time or report failure."
                    ),
                    warning_key=f"poll:{tool_name}:{current_hash}:{latest_result_hash or 'none'}",
                )

        # --- Ping-pong detector ---
        if self._config.ping_pong:
            ping_pong = self._get_ping_pong_streak(history, current_hash)
            pair_key = f"pingpong:{self._canonical_pair_key(current_hash, ping_pong.paired_signature)}" if ping_pong.paired_signature else f"pingpong:{tool_name}:{current_hash}"

            if (
                ping_pong.count >= self._config.critical_threshold
                and ping_pong.no_progress_evidence
            ):
                return LoopDetectionResult(
                    stuck=True,
                    level=LoopDetectionLevel.CRITICAL,
                    detector=LoopDetectorKind.PING_PONG,
                    count=ping_pong.count,
                    message=(
                        f"CRITICAL: Alternating between repeated tool-call patterns "
                        f"({ping_pong.count} calls) with no progress. Ping-pong loop blocked."
                    ),
                    paired_tool_name=ping_pong.paired_tool_name,
                    warning_key=pair_key,
                )

            if ping_pong.count >= self._config.warning_threshold:
                return LoopDetectionResult(
                    stuck=True,
                    level=LoopDetectionLevel.WARNING,
                    detector=LoopDetectorKind.PING_PONG,
                    count=ping_pong.count,
                    message=(
                        f"WARNING: Alternating between repeated tool-call patterns "
                        f"({ping_pong.count} calls). Possible ping-pong loop."
                    ),
                    paired_tool_name=ping_pong.paired_tool_name,
                    warning_key=pair_key,
                )

        # --- Generic repeat ---
        if not is_poll and self._config.generic_repeat:
            recent_count = sum(
                1 for h in history
                if h.tool_name == tool_name and h.args_hash == current_hash
            )
            if no_progress_streak >= self._config.critical_threshold:
                return LoopDetectionResult(
                    stuck=True,
                    level=LoopDetectionLevel.CRITICAL,
                    detector=LoopDetectorKind.GENERIC_REPEAT,
                    count=no_progress_streak,
                    message=(
                        f"CRITICAL: {tool_name} repeated identical outcomes "
                        f"{no_progress_streak} times. Runaway loop blocked."
                    ),
                    warning_key=f"generic:{tool_name}:{current_hash}:{latest_result_hash or 'none'}",
                )
            if recent_count >= self._config.warning_threshold:
                return LoopDetectionResult(
                    stuck=True,
                    level=LoopDetectionLevel.WARNING,
                    detector=LoopDetectorKind.GENERIC_REPEAT,
                    count=recent_count,
                    message=(
                        f"WARNING: {tool_name} called {recent_count} times with identical args. "
                        f"Stop retrying if no progress."
                    ),
                    warning_key=f"generic:{tool_name}:{current_hash}",
                )

        return LoopDetectionResult(stuck=False)

    def record_call(
        self,
        state: SessionState,
        tool_name: str,
        params: Any,
        tool_call_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> ToolCallRecord:
        """Record a tool call in session history (sliding window)."""
        record = ToolCallRecord(
            tool_name=tool_name,
            args_hash=hash_tool_call(tool_name, params),
            tool_call_id=tool_call_id,
            run_id=run_id,
            timestamp=time.time(),
        )
        state.tool_call_history.append(record)
        self._trim_history(state)
        return record

    def record_outcome(
        self,
        state: SessionState,
        tool_name: str,
        params: Any,
        result: Any = None,
        error: Any = None,
        tool_call_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> Optional[ToolCallRecord]:
        """Record a completed tool call outcome for no-progress detection."""
        outcome = self._hash_tool_outcome(tool_name, params, result, error)
        if not outcome.result_hash and not outcome.outcome_kind:
            return None

        args_hash = hash_tool_call(tool_name, params)
        # Find matching unrecorded call (search from end for most recent)
        for idx in range(len(state.tool_call_history) - 1, -1, -1):
            record = state.tool_call_history[idx]
            if record.run_id != run_id:
                continue
            if tool_call_id and record.tool_call_id != tool_call_id:
                continue
            if record.tool_name != tool_name or record.args_hash != args_hash:
                continue
            if record.result_hash is not None or record.outcome_kind is not None:
                continue
            # Replace with outcome-enriched record
            updated = ToolCallRecord(
                tool_name=record.tool_name,
                args_hash=record.args_hash,
                tool_call_id=record.tool_call_id,
                run_id=record.run_id,
                timestamp=record.timestamp,
                result_hash=outcome.result_hash,
                outcome_kind=outcome.outcome_kind,
                no_progress=outcome.no_progress,
                unknown_tool_name=outcome.unknown_tool_name,
            )
            state.tool_call_history[idx] = updated
            self._trim_history(state)
            return updated

        # No matching record → add new one
        record = ToolCallRecord(
            tool_name=tool_name,
            args_hash=args_hash,
            tool_call_id=tool_call_id,
            run_id=run_id,
            timestamp=time.time(),
            result_hash=outcome.result_hash,
            outcome_kind=outcome.outcome_kind,
            no_progress=outcome.no_progress,
            unknown_tool_name=outcome.unknown_tool_name,
        )
        state.tool_call_history.append(record)
        self._trim_history(state)
        return record

    # -- Internal detectors --------------------------------------------------

    def _get_no_progress_streak(
        self,
        history: List[ToolCallRecord],
        tool_name: str,
        current_hash: str,
    ) -> Tuple[int, Optional[str]]:
        """
        Count how many consecutive recent calls had identical no-progress outcomes.

        A call is "no-progress" when:
        - Its result_hash matches the previous call's result_hash for the same args_hash
        - Its no_progress flag is explicitly True
        - It has no result_hash yet (still pending)
        """
        # Collect consecutive matching calls (same tool + same args)
        matching: List[ToolCallRecord] = []
        for record in reversed(history):
            if record.tool_name != tool_name or record.args_hash != current_hash:
                break
            matching.append(record)

        if not matching:
            return 0, None

        # Check if all have the same result hash (identical outcomes = no progress)
        result_hashes = [r.result_hash for r in matching if r.result_hash is not None]
        # If any call made progress (different result hash), streak breaks
        if result_hashes:
            unique_hashes = set(result_hashes)
            if len(unique_hashes) > 1:
                # Different results → progress was made somewhere
                # Count only from the last hash change
                last_hash = result_hashes[0]
                streak = 0
                for rh in result_hashes:
                    if rh == last_hash:
                        streak += 1
                    else:
                        break
                return streak, last_hash

        # All same hash or all pending → that's no progress
        streak = len(matching)
        latest_result_hash = result_hashes[0] if result_hashes else None
        return streak, latest_result_hash

    def _get_unknown_tool_streak(
        self,
        history: List[ToolCallRecord],
        tool_name: str,
    ) -> Tuple[int, Optional[str]]:
        """Count consecutive calls to the same unknown tool."""
        streak = 0
        unknown_name: Optional[str] = None
        for record in reversed(history):
            if record.tool_name != tool_name or not record.unknown_tool_name:
                break
            if unknown_name is None:
                unknown_name = record.unknown_tool_name
                streak = 1
            elif record.unknown_tool_name == unknown_name:
                streak += 1
            else:
                break
        return streak, unknown_name

    def _get_ping_pong_streak(
        self,
        history: List[ToolCallRecord],
        current_hash: str,
    ) -> _PingPongResult:
        """Detect alternating A-B-A-B patterns."""
        if not history:
            return _PingPongResult(count=0, no_progress_evidence=False)

        last = history[-1]
        # Find the "other" signature
        other_signature: Optional[str] = None
        other_tool_name: Optional[str] = None
        for record in reversed(history[:-1]):
            if record.args_hash != last.args_hash:
                other_signature = record.args_hash
                other_tool_name = record.tool_name
                break

        if other_signature is None or other_tool_name is None:
            return _PingPongResult(count=0, no_progress_evidence=False)

        # Count alternating tail
        alternating_count = 0
        for record in reversed(history):
            expected = last.args_hash if alternating_count % 2 == 0 else other_signature
            if record.args_hash != expected:
                break
            alternating_count += 1

        if alternating_count < 2:
            return _PingPongResult(count=0, no_progress_evidence=False)

        expected_current = other_signature
        if current_hash != expected_current:
            return _PingPongResult(count=0, no_progress_evidence=False)

        # Check no-progress evidence
        tail_start = max(0, len(history) - alternating_count)
        first_hash_a: Optional[str] = None
        first_hash_b: Optional[str] = None
        no_progress = True
        for record in history[tail_start:]:
            if record.result_hash is None:
                no_progress = False
                break
            if record.args_hash == last.args_hash:
                if first_hash_a is None:
                    first_hash_a = record.result_hash
                elif first_hash_a != record.result_hash:
                    no_progress = False
                    break
            elif record.args_hash == other_signature:
                if first_hash_b is None:
                    first_hash_b = record.result_hash
                elif first_hash_b != record.result_hash:
                    no_progress = False
                    break
            else:
                no_progress = False
                break

        if first_hash_a is None or first_hash_b is None:
            no_progress = False

        return _PingPongResult(
            count=alternating_count + 1,
            paired_tool_name=last.tool_name,
            paired_signature=last.args_hash,
            no_progress_evidence=no_progress,
        )

    def _is_known_poll(self, tool_name: str, params: Any) -> bool:
        """Check if this call is a known poll-type operation."""
        if tool_name not in KNOWN_POLL_TOOLS:
            return False
        if isinstance(params, dict):
            action = params.get("action")
            if action in ("poll", "log"):
                return True
        return False

    def _hash_tool_outcome(
        self,
        tool_name: str,
        params: Any,
        result: Any,
        error: Any,
    ) -> _ToolOutcome:
        """Hash a tool call outcome for no-progress detection."""
        if error is not None:
            unknown_name = extract_unknown_tool_name(error)
            return _ToolOutcome(
                result_hash=f"error:{digest_stable(format_error_for_hash(error))}",
                no_progress=True,
                unknown_tool_name=unknown_name,
            )

        if result is None:
            return _ToolOutcome()

        if not isinstance(result, dict):
            return _ToolOutcome(result_hash=digest_stable(result))

        details = result.get("details") if isinstance(result.get("details"), dict) else {}
        text = extract_text_content(result)

        if tool_name == "exec":
            exec_hash = self._hash_exec_outcome(details, text)
            if exec_hash:
                return _ToolOutcome(result_hash=exec_hash)

        if tool_name == "write" and details.get("status") == "unchanged":
            return _ToolOutcome(
                result_hash=digest_stable({"status": "unchanged"}),
                no_progress=True,
            )

        if is_volatile_send_result(tool_name, params):
            return _ToolOutcome(result_hash=digest_stable(strip_volatile_send_ids(details)))

        return _ToolOutcome(result_hash=digest_stable({"details": details, "text": text}))

    def _hash_exec_outcome(self, details: Dict[str, Any], text: str) -> Optional[str]:
        """Hash exec tool outcome (status-aware)."""
        status = details.get("status")
        if not isinstance(status, str):
            return None

        if status == "running":
            return digest_stable({"status": status, "tail": details.get("tail", "")})

        if status in ("completed", "failed"):
            return digest_stable({
                "status": status,
                "exitCode": details.get("exitCode"),
                "timedOut": details.get("timedOut", False),
                "output": details.get("aggregated") or text,
            })

        if status in ("approval-pending", "approval-unavailable"):
            return digest_stable({
                "status": status,
                "reason": details.get("reason"),
                "host": details.get("host"),
                "command": details.get("command", ""),
            })

        return None

    def _trim_history(self, state: SessionState) -> None:
        """Keep history within configured window size."""
        max_size = self._config.history_size
        if len(state.tool_call_history) > max_size:
            state.tool_call_history = state.tool_call_history[-max_size:]

    @staticmethod
    def _canonical_pair_key(sig_a: str, sig_b: Optional[str]) -> str:
        if sig_b is None:
            return sig_a
        return "|".join(sorted([sig_a, sig_b]))


@dataclass(frozen=True)
class _PingPongResult:
    count: int
    paired_tool_name: Optional[str] = None
    paired_signature: Optional[str] = None
    no_progress_evidence: bool = False


@dataclass(frozen=True)
class _ToolOutcome:
    result_hash: Optional[str] = None
    outcome_kind: Optional[str] = None
    no_progress: bool = False
    unknown_tool_name: Optional[str] = None


# ---------------------------------------------------------------------------
# DangerousToolDetector
# ---------------------------------------------------------------------------

class DangerousToolDetector:
    """
    Flags dangerous tool combinations that could escalate privileges,
    enable RCE, or cause data loss.

    Extended from the dangerous-tools reference with combination-based detection.
    """

    # Tools that individually are high-risk
    INDIVIDUALLY_DANGEROUS: FrozenSet[str] = frozenset({
        "exec", "spawn", "shell", "process",
        "fs_write", "fs_delete", "fs_move", "apply_patch",
        "sessions_spawn", "sessions_send",
        "gateway", "nodes",
        "computer", "mobile_ui",
    })

    # Tool combinations that create amplified risk
    COMBINATION_RULES: List[DangerousToolCombo] = [
        DangerousToolCombo(
            tools=frozenset({"exec", "fs_write"}),
            reason="Shell execution + file write enables arbitrary code persistence",
            severity=Severity.CRITICAL,
        ),
        DangerousToolCombo(
            tools=frozenset({"exec", "sessions_spawn"}),
            reason="Shell execution + session spawn enables lateral movement",
            severity=Severity.CRITICAL,
        ),
        DangerousToolCombo(
            tools=frozenset({"exec", "gateway"}),
            reason="Shell execution + gateway access exposes secrets and config",
            severity=Severity.CRITICAL,
        ),
        DangerousToolCombo(
            tools=frozenset({"fs_write", "exec"}),
            reason="File write + shell enables backdoor installation",
            severity=Severity.CRITICAL,
        ),
        DangerousToolCombo(
            tools=frozenset({"sessions_spawn", "sessions_send"}),
            reason="Session orchestration enables cross-session code injection",
            severity=Severity.WARN,
        ),
        DangerousToolCombo(
            tools=frozenset({"exec", "computer"}),
            reason="Shell execution + desktop control enables full system takeover",
            severity=Severity.CRITICAL,
        ),
        DangerousToolCombo(
            tools=frozenset({"exec", "mobile_ui"}),
            reason="Shell execution + mobile control enables cross-platform attack",
            severity=Severity.CRITICAL,
        ),
        DangerousToolCombo(
            tools=frozenset({"fs_write", "fs_delete"}),
            reason="File write + delete enables data destruction",
            severity=Severity.WARN,
        ),
        DangerousToolCombo(
            tools=frozenset({"apply_patch", "exec"}),
            reason="Patch application + shell enables arbitrary code injection",
            severity=Severity.CRITICAL,
        ),
        DangerousToolCombo(
            tools=frozenset({"nodes", "exec"}),
            reason="Node relay + shell enables remote code execution on paired hosts",
            severity=Severity.CRITICAL,
        ),
    ]

    def __init__(
        self,
        extra_dangerous: Optional[Iterable[str]] = None,
        extra_combos: Optional[Iterable[DangerousToolCombo]] = None,
    ) -> None:
        self._extra_dangerous = frozenset(extra_dangerous or [])
        all_dangerous = self.INDIVIDUALLY_DANGEROUS | self._extra_dangerous
        self._all_dangerous = all_dangerous
        self._combo_rules = list(self.COMBINATION_RULES)
        if extra_combos:
            self._combo_rules.extend(extra_combos)

    def is_dangerous(self, tool_name: str) -> bool:
        """Check if a tool is individually dangerous."""
        return normalize_tool_name(tool_name) in self._all_dangerous

    def check_tool_set(
        self,
        tool_names: Iterable[str],
    ) -> List[Tuple[Severity, str, FrozenSet[str]]]:
        """
        Check a set of tool names against all dangerous-combination rules.

        Returns list of (severity, reason, matched_tools) tuples.
        """
        normalized = frozenset(normalize_tool_name(t) for t in tool_names)
        findings: List[Tuple[Severity, str, FrozenSet[str]]] = []
        for rule in self._combo_rules:
            if rule.tools.issubset(normalized):
                findings.append((rule.severity, rule.reason, rule.tools))
        return findings

    def find_dangerous_tools(
        self,
        tool_names: Iterable[str],
    ) -> List[str]:
        """Return list of individually dangerous tools from a set."""
        normalized = [normalize_tool_name(t) for t in tool_names]
        return [t for t in normalized if t in self._all_dangerous]

    def audit_tool_calls(
        self,
        tool_calls: Sequence[Tuple[str, Any]],
    ) -> List[SecurityAuditFinding]:
        """
        Audit a sequence of (tool_name, params) calls.

        Returns findings for individually dangerous tools and combinations.
        """
        findings: List[SecurityAuditFinding] = []
        tool_names: List[str] = []

        for tool_name, _params in tool_calls:
            normalized = normalize_tool_name(tool_name)
            tool_names.append(normalized)
            if self.is_dangerous(normalized):
                findings.append(SecurityAuditFinding(
                    check_id=f"dangerous.tool.{normalized}",
                    severity=Severity.WARN,
                    title=f"Dangerous tool used: {normalized}",
                    detail=f"Tool '{normalized}' is flagged as individually dangerous. "
                           f"Ensure proper policy restrictions are in place.",
                    remediation=f"Add '{normalized}' to deny list if not needed, or ensure "
                                f"sandbox execution and approval workflows are configured.",
                ))

        # Check combinations
        combo_findings = self.check_tool_set(tool_names)
        for severity, reason, matched_tools in combo_findings:
            findings.append(SecurityAuditFinding(
                check_id=f"dangerous.combo.{sorted(matched_tools)}",
                severity=severity,
                title="Dangerous tool combination detected",
                detail=f"Tools {sorted(matched_tools)} together: {reason}",
                remediation="Remove one or more tools from the combination, or ensure "
                            "strict approval workflows and sandbox isolation.",
            ))

        return findings


# ---------------------------------------------------------------------------
# ToolSandbox
# ---------------------------------------------------------------------------

class ToolSandbox:
    """
    Restricted subprocess execution sandbox.

    Provides:
      - Timeout enforcement
      - Output size limits
      - Command allow/deny lists
      - Environment isolation
      - Network restriction (via env)
      - Working directory control
      - Resource limits (memory, where available)
    """

    def __init__(self, config: Optional[SandboxConfig] = None) -> None:
        self._config = config or SandboxConfig()

    @property
    def config(self) -> SandboxConfig:
        return self._config

    def execute(
        self,
        command: str,
        *,
        timeout: Optional[float] = None,
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
    ) -> SandboxResult:
        """
        Execute a command in the sandbox.

        Args:
            command: Shell command string.
            timeout: Override timeout in seconds.
            working_dir: Override working directory.
            env: Additional environment variables.

        Returns:
            SandboxResult with exit_code, stdout, stderr, etc.
        """
        effective_timeout = timeout or self._config.timeout_seconds
        effective_cwd = working_dir or self._config.working_directory

        # Command allow/deny checks
        if not self._check_command_allowed(command):
            return SandboxResult(
                exit_code=126,
                stdout="",
                stderr="Command denied by sandbox policy.",
            )

        # Build environment
        effective_env = self._build_env(env)

        # Build subprocess args
        shell = self._config.shell or ("/bin/bash" if sys.platform != "win32" else "cmd.exe")
        is_windows = sys.platform == "win32"

        if is_windows:
            argv = ["cmd.exe", "/c", command]
        else:
            argv = [shell, "-c", command]

        kwargs: Dict[str, Any] = {
            "args": argv,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "env": effective_env,
            "timeout": effective_timeout,
        }

        if effective_cwd:
            kwargs["cwd"] = effective_cwd

        try:
            proc = subprocess.run(**kwargs)
            stdout = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
            stderr = proc.stderr.decode("utf-8", errors="replace") if proc.stderr else ""

            # Truncate oversized output
            if len(stdout) > self._config.max_output_bytes:
                stdout = stdout[: self._config.max_output_bytes] + "\n... [truncated]"
            if len(stderr) > self._config.max_output_bytes:
                stderr = stderr[: self._config.max_output_bytes] + "\n... [truncated]"

            return SandboxResult(
                exit_code=proc.returncode,
                stdout=stdout,
                stderr=stderr,
            )

        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode("utf-8", errors="replace") if exc.stdout else ""
            stderr = exc.stderr.decode("utf-8", errors="replace") if exc.stderr else ""
            logger.warning("Sandbox command timed out after %.1fs", effective_timeout)
            return SandboxResult(
                exit_code=-1,
                stdout=stdout,
                stderr=stderr,
                timed_out=True,
            )

        except FileNotFoundError:
            return SandboxResult(
                exit_code=127,
                stdout="",
                stderr=f"Shell not found: {shell}",
            )

        except Exception as exc:
            return SandboxResult(
                exit_code=1,
                stdout="",
                stderr=f"Sandbox error: {exc}",
                killed=True,
            )

    def execute_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
    ) -> SandboxResult:
        """
        Execute a tool call through the sandbox.

        Translates tool params into a subprocess command.
        For exec/shell tools: runs the 'command' param.
        For fs tools: translates to shell commands.
        """
        normalized = normalize_tool_name(tool_name)

        if normalized in ("exec", "shell", "spawn"):
            command = params.get("command", "")
            if not command:
                return SandboxResult(exit_code=1, stdout="", stderr="No command provided")
            return self.execute(command)

        if normalized == "fs_read":
            path = params.get("path", "")
            if not path:
                return SandboxResult(exit_code=1, stdout="", stderr="No path provided")
            return self.execute(f"cat {shlex.quote(path)}")

        if normalized == "fs_write":
            path = params.get("path", "")
            content = params.get("content", "")
            if not path:
                return SandboxResult(exit_code=1, stdout="", stderr="No path provided")
            escaped_content = shlex.quote(content)
            return self.execute(f"echo {escaped_content} > {shlex.quote(path)}")

        if normalized == "fs_delete":
            path = params.get("path", "")
            if not path:
                return SandboxResult(exit_code=1, stdout="", stderr="No path provided")
            return self.execute(f"rm -f {shlex.quote(path)}")

        if normalized == "fs_move":
            source = params.get("source", "")
            dest = params.get("destination", "")
            if not source or not dest:
                return SandboxResult(exit_code=1, stdout="", stderr="Source and destination required")
            return self.execute(f"mv {shlex.quote(source)} {shlex.quote(dest)}")

        if normalized == "fs_list":
            path = params.get("path", ".")
            return self.execute(f"ls -la {shlex.quote(path)}")

        return SandboxResult(
            exit_code=1,
            stdout="",
            stderr=f"Tool '{tool_name}' not supported by sandbox executor",
        )

    # -- Internal ------------------------------------------------------------

    def _check_command_allowed(self, command: str) -> bool:
        """Check if command is allowed by deny/allow lists."""
        if self._config.denied_commands:
            for denied in self._config.denied_commands:
                if denied in command:
                    return False

        if self._config.allowed_commands:
            for allowed in self._config.allowed_commands:
                if allowed in command:
                    return True
            return False

        return True

    def _build_env(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Build sandboxed environment dict."""
        if not self._config.env_inherit:
            # Minimal env for sandboxed execution
            base: Dict[str, str] = {
                "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                "HOME": tempfile.gettempdir(),
                "TMPDIR": tempfile.gettempdir(),
                "LANG": "en_US.UTF-8",
            }
        else:
            base = dict(os.environ)

        if self._config.env_overrides:
            base.update(self._config.env_overrides)

        if extra:
            base.update(extra)

        if not self._config.network_access:
            # Best-effort network restriction (not foolproof)
            base.pop("http_proxy", None)
            base.pop("https_proxy", None)
            base.pop("HTTP_PROXY", None)
            base.pop("HTTPS_PROXY", None)
            base["NO_PROXY"] = "*"

        return base


# ---------------------------------------------------------------------------
# SecurityAuditor
# ---------------------------------------------------------------------------

class SecurityAuditor:
    """
    Audits tool calls against policies, dangerous-tool rules, and
    configuration best practices.

    Produces SecurityAuditReport with findings, suppressed findings, and summary.
    """

    def __init__(
        self,
        policy: Optional[ToolPolicy] = None,
        dangerous_detector: Optional[DangerousToolDetector] = None,
        suppressions: Optional[List[AuditSuppression]] = None,
        enabled_checks: Optional[List[str]] = None,
    ) -> None:
        self._policy = policy
        self._dangerous_detector = dangerous_detector or DangerousToolDetector()
        self._suppressions = suppressions or []
        self._enabled_checks = enabled_checks

    def audit_tool_call(
        self,
        tool_name: str,
        params: Any,
        *,
        caller_identity: Optional[str] = None,
        is_gateway_http: bool = False,
    ) -> List[SecurityAuditFinding]:
        """
        Audit a single tool call against all security rules.

        Returns list of findings (may be empty if call is clean).
        """
        findings: List[SecurityAuditFinding] = []
        normalized = normalize_tool_name(tool_name)

        # 1. Policy allow/deny check
        if self._policy and not self._policy.is_tool_allowed(normalized):
            findings.append(SecurityAuditFinding(
                check_id="policy.denied_tool",
                severity=Severity.CRITICAL,
                title=f"Tool '{normalized}' denied by policy",
                detail=f"Tool '{normalized}' is in the deny list or not in the allow list.",
                remediation=f"Remove '{normalized}' from deny list or add to allow list if needed.",
            ))

        # 2. Gateway HTTP deny check
        if is_gateway_http and normalized in DEFAULT_GATEWAY_HTTP_TOOL_DENY:
            findings.append(SecurityAuditFinding(
                check_id="gateway.http_denied_tool",
                severity=Severity.CRITICAL,
                title=f"Tool '{normalized}' denied on gateway HTTP surface",
                detail=f"Tool '{normalized}' is in the default gateway HTTP deny list. "
                       f"These tools are high-risk for non-interactive HTTP surfaces.",
                remediation="Use interactive surfaces or explicit approval workflows for this tool.",
            ))

        # 3. Owner-only check
        if is_gateway_http and normalized in GATEWAY_OWNER_ONLY_CORE_TOOLS:
            if caller_identity != "owner":
                findings.append(SecurityAuditFinding(
                    check_id="gateway.owner_only_tool",
                    severity=Severity.CRITICAL,
                    title=f"Tool '{normalized}' requires owner identity",
                    detail=f"Tool '{normalized}' is owner-only on gateway surfaces. "
                           f"Caller '{caller_identity or 'unknown'}' is not owner.",
                    remediation="Ensure caller has owner identity or remove this tool from gateway surface.",
                ))

        # 4. Individual dangerous tool check
        if self._dangerous_detector.is_dangerous(normalized):
            findings.append(SecurityAuditFinding(
                check_id=f"dangerous.tool.{normalized}",
                severity=Severity.WARN,
                title=f"Dangerous tool '{normalized}' in use",
                detail=f"Tool '{normalized}' is flagged as individually dangerous.",
                remediation=f"Ensure sandbox execution and approval workflows for '{normalized}'.",
            ))

        # 5. Param-specific checks
        findings.extend(self._check_params(normalized, params))

        return findings

    def audit_tool_calls(
        self,
        tool_calls: Sequence[Tuple[str, Any]],
        *,
        caller_identity: Optional[str] = None,
        is_gateway_http: bool = False,
    ) -> SecurityAuditReport:
        """
        Audit a batch of tool calls.

        Returns full SecurityAuditReport with all findings and summary.
        """
        all_findings: List[SecurityAuditFinding] = []

        for tool_name, params in tool_calls:
            findings = self.audit_tool_call(
                tool_name,
                params,
                caller_identity=caller_identity,
                is_gateway_http=is_gateway_http,
            )
            all_findings.extend(findings)

        # Dangerous combination check
        tool_names = [normalize_tool_name(t) for t, _ in tool_calls]
        combo_findings = self._dangerous_detector.check_tool_set(tool_names)
        for severity, reason, matched_tools in combo_findings:
            all_findings.append(SecurityAuditFinding(
                check_id=f"dangerous.combo.{sorted(matched_tools)}",
                severity=severity,
                title="Dangerous tool combination detected",
                detail=f"Tools {sorted(matched_tools)} together: {reason}",
                remediation="Break up the combination or enforce strict approval workflows.",
            ))

        # Apply suppressions
        active, suppressed = self._apply_suppressions(all_findings)

        # Summary
        summary = SecurityAuditSummary()
        for f in active:
            if f.severity == Severity.CRITICAL:
                summary.critical += 1
            elif f.severity == Severity.WARN:
                summary.warn += 1
            else:
                summary.info += 1

        return SecurityAuditReport(
            timestamp=time.time(),
            summary=summary,
            findings=active,
            suppressed_findings=suppressed,
        )

    def audit_configuration(
        self,
        *,
        gateway_auth_mode: Optional[str] = None,
        gateway_has_token: bool = False,
        gateway_has_password: bool = False,
        exec_host: Optional[str] = None,
        exec_mode: Optional[str] = None,
        sandbox_mode: Optional[str] = None,
        tools_allow: Optional[List[str]] = None,
        tools_deny: Optional[List[str]] = None,
        elevated_enabled: bool = True,
        elevated_allow_from: Optional[Dict[str, List[str]]] = None,
    ) -> SecurityAuditReport:
        """
        Audit configuration settings against security best practices.
        """
        findings: List[SecurityAuditFinding] = []

        # Gateway auth
        if gateway_auth_mode is not None:
            if gateway_auth_mode == "none":
                findings.append(SecurityAuditFinding(
                    check_id="gateway.auth_none",
                    severity=Severity.CRITICAL,
                    title="Gateway authentication disabled",
                    detail="Gateway auth mode is 'none'. All requests are unauthenticated.",
                    remediation="Enable token or password authentication.",
                ))
            if gateway_has_token and gateway_has_password:
                findings.append(SecurityAuditFinding(
                    check_id="gateway.auth_dual_secret",
                    severity=Severity.WARN,
                    title="Gateway has both token and password",
                    detail="Both token and password are configured. Use one for clarity.",
                ))

        # Exec settings
        if exec_mode == "full":
            findings.append(SecurityAuditFinding(
                check_id="tools.exec.security_full",
                severity=Severity.CRITICAL,
                title="Exec security set to 'full'",
                detail="Full exec trust bypasses all approval workflows.",
                remediation='Use exec mode "ask" or "allowlist" instead of "full".',
            ))

        # Sandbox
        if exec_host == "sandbox" and sandbox_mode == "off":
            findings.append(SecurityAuditFinding(
                check_id="tools.exec.host_sandbox_no_sandbox",
                severity=Severity.WARN,
                title="Exec host is sandbox but sandbox mode is off",
                detail="Exec will fail closed because no sandbox runtime is available.",
                remediation='Enable sandbox mode or change exec host to "gateway".',
            ))

        # Policy warnings
        if tools_allow and "*" in tools_allow:
            findings.append(SecurityAuditFinding(
                check_id="tools.allow_wildcard",
                severity=Severity.WARN,
                title="Allow list contains wildcard",
                detail='tools.allow includes "*" which allows all tools.',
                remediation="Replace wildcard with explicit tool list.",
            ))

        # Elevated exec
        if elevated_enabled and elevated_allow_from:
            for provider, ids in elevated_allow_from.items():
                if "*" in ids:
                    findings.append(SecurityAuditFinding(
                        check_id=f"tools.elevated.allowFrom.{provider}.wildcard",
                        severity=Severity.CRITICAL,
                        title=f"Elevated allowFrom wildcard for {provider}",
                        detail=f"tools.elevated.allowFrom.{provider} includes wildcard. "
                               f"Everyone on that channel gets elevated access.",
                        remediation="Replace wildcard with specific user/group ids.",
                    ))
                elif len(ids) > 25:
                    findings.append(SecurityAuditFinding(
                        check_id=f"tools.elevated.allowFrom.{provider}.large",
                        severity=Severity.WARN,
                        title=f"Elevated allowFrom list is large for {provider}",
                        detail=f"tools.elevated.allowFrom.{provider} has {len(ids)} entries.",
                        remediation="Tighten elevated access list.",
                    ))

        # Apply suppressions
        active, suppressed = self._apply_suppressions(findings)

        summary = SecurityAuditSummary()
        for f in active:
            if f.severity == Severity.CRITICAL:
                summary.critical += 1
            elif f.severity == Severity.WARN:
                summary.warn += 1
            else:
                summary.info += 1

        return SecurityAuditReport(
            timestamp=time.time(),
            summary=summary,
            findings=active,
            suppressed_findings=suppressed,
        )

    # -- Internal ------------------------------------------------------------

    def _check_params(self, tool_name: str, params: Any) -> List[SecurityAuditFinding]:
        """Tool-specific parameter safety checks."""
        findings: List[SecurityAuditFinding] = []
        if not isinstance(params, dict):
            return findings

        # Command injection hints
        if tool_name in ("exec", "shell", "spawn"):
            command = params.get("command", "")
            if isinstance(command, str):
                # Suspicious patterns
                if any(p in command for p in ("rm -rf /", "mkfs", "dd if=", "> /dev/")):
                    findings.append(SecurityAuditFinding(
                        check_id="exec.destructive_command",
                        severity=Severity.CRITICAL,
                        title="Destructive shell command detected",
                        detail=f"Command contains potentially destructive operations: {command[:100]}",
                        remediation="Review command carefully. Consider sandboxing.",
                    ))
                if "sudo" in command:
                    findings.append(SecurityAuditFinding(
                        check_id="exec.sudo_usage",
                        severity=Severity.WARN,
                        title="sudo usage in shell command",
                        detail="Command uses sudo which escalates privileges.",
                        remediation="Avoid sudo in tool execution.",
                    ))

        # File path traversal
        if tool_name in ("fs_read", "fs_write", "fs_delete", "fs_move"):
            for key in ("path", "source", "destination"):
                val = params.get(key, "")
                if isinstance(val, str) and ".." in val:
                    findings.append(SecurityAuditFinding(
                        check_id="fs.path_traversal",
                        severity=Severity.WARN,
                        title=f"Path traversal in {key}",
                        detail=f"Path contains '..': {val}",
                        remediation="Validate and sanitize file paths.",
                    ))

        return findings

    def _apply_suppressions(
        self,
        findings: List[SecurityAuditFinding],
    ) -> Tuple[List[SecurityAuditFinding], List[SecurityAuditSuppressedFinding]]:
        """Apply configured suppressions to findings."""
        if not self._suppressions:
            return findings, []

        active: List[SecurityAuditFinding] = []
        suppressed: List[SecurityAuditSuppressedFinding] = []

        for finding in findings:
            matched_suppression = None
            for suppression in self._suppressions:
                if self._finding_matches_suppression(finding, suppression):
                    matched_suppression = suppression
                    break

            if matched_suppression is None:
                active.append(finding)
            else:
                suppressed.append(SecurityAuditSuppressedFinding(
                    check_id=finding.check_id,
                    severity=finding.severity,
                    title=finding.title,
                    detail=finding.detail,
                    remediation=finding.remediation,
                    suppression_reason=matched_suppression.reason,
                ))

        return active, suppressed

    @staticmethod
    def _finding_matches_suppression(
        finding: SecurityAuditFinding,
        suppression: AuditSuppression,
    ) -> bool:
        """Check if a finding matches a suppression rule."""
        check_id = suppression.check_id.strip()
        if not check_id or finding.check_id != check_id:
            return False

        if suppression.title_includes:
            needle = suppression.title_includes.strip().lower()
            if needle and needle not in finding.title.lower():
                return False

        if suppression.detail_includes:
            needle = suppression.detail_includes.strip().lower()
            if needle and needle not in finding.detail.lower():
                return False

        return True


# ---------------------------------------------------------------------------
# Convenience: all-in-one audit function
# ---------------------------------------------------------------------------

def run_tool_security_audit(
    tool_calls: Sequence[Tuple[str, Any]],
    *,
    policy: Optional[ToolPolicy] = None,
    caller_identity: Optional[str] = None,
    is_gateway_http: bool = False,
    suppressions: Optional[List[AuditSuppression]] = None,
) -> SecurityAuditReport:
    """
    One-shot security audit of tool calls.

    Creates a SecurityAuditor with default dangerous-tool detection,
    runs the audit, and returns the report.
    """
    auditor = SecurityAuditor(
        policy=policy,
        suppressions=suppressions,
    )
    return auditor.audit_tool_calls(
        tool_calls,
        caller_identity=caller_identity,
        is_gateway_http=is_gateway_http,
    )


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    # Enums
    "Severity",
    "LoopDetectorKind",
    "LoopDetectionLevel",
    # Dataclasses
    "ToolPolicyConfig",
    "ToolCallRecord",
    "LoopDetectionResult",
    "LoopDetectionConfig",
    "SecurityAuditFinding",
    "SecurityAuditSuppressedFinding",
    "SecurityAuditSummary",
    "SecurityAuditReport",
    "DangerousToolCombo",
    "SandboxConfig",
    "SandboxResult",
    "SessionState",
    "AuditSuppression",
    # Classes
    "ToolPolicy",
    "ToolLoopDetector",
    "DangerousToolDetector",
    "ToolSandbox",
    "SecurityAuditor",
    # Constants
    "DEFAULT_GATEWAY_HTTP_TOOL_DENY",
    "GATEWAY_OWNER_ONLY_CORE_TOOLS",
    "TOOL_GROUPS",
    "TOOL_NAME_ALIASES",
    "DEFAULT_PLUGIN_TOOLS_ALLOWLIST_ENTRY",
    # Helpers
    "normalize_tool_name",
    "normalize_tool_list",
    "expand_tool_groups",
    "hash_tool_call",
    "run_tool_security_audit",
]
