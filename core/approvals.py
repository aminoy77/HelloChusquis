"""Human-approval controls for high-impact agent tool calls.

Approval is intentionally local to an agent session. Requests are opaque,
short-lived, idempotent while pending, and consumed before execution so a
confirmation cannot be replayed.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
import secrets
import threading
import time
from typing import Any, Callable, Optional

from core.tool_policy import digest_stable, normalize_tool_name


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    CANCELLED = "cancelled"
    EXECUTING = "executing"
    EXECUTED = "executed"
    EXPIRED = "expired"


@dataclass
class ApprovalRequest:
    """A single high-impact tool call awaiting a human decision."""

    id: str
    tool_name: str
    tool_args: dict[str, Any]
    reason: str
    created_at: float
    expires_at: float
    status: ApprovalStatus = ApprovalStatus.PENDING
    decided_at: Optional[float] = None
    result_summary: Optional[str] = None

    def to_public_dict(self) -> dict[str, Any]:
        """Return a JSON-safe view without leaking credentials to the UI."""
        data = asdict(self)
        data["status"] = self.status.value
        data["tool_args"] = redact_sensitive_data(self.tool_args)
        data.pop("result_summary", None)
        return data


_SENSITIVE_KEYWORDS = ("api_key", "authorization", "cookie", "password", "secret", "token")


def redact_sensitive_data(value: Any) -> Any:
    """Recursively redact common credential-bearing argument fields."""
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if any(keyword in str(key).lower() for keyword in _SENSITIVE_KEYWORDS):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_sensitive_data(item)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive_data(item) for item in value]
    if isinstance(value, tuple):
        return [redact_sensitive_data(item) for item in value]
    return value


_MUTATING_FILE_ACTIONS = frozenset({"write", "delete", "create_dir"})
_MUTATING_BROWSER_ACTIONS = frozenset({"submit_form", "upload_file"})
_MUTATING_PREFIXES = (
    "create", "update", "delete", "remove", "send", "post", "publish",
    "invite", "transfer", "charge", "refund", "purchase", "checkout",
    "deploy", "destroy", "start", "stop", "restart", "invoke", "trigger",
    "write", "set", "enable", "disable", "grant", "revoke",
)


def approval_reason(tool_name: str, tool_args: dict[str, Any]) -> Optional[str]:
    """Classify calls that can change local or external state.

    Read-only operations stay autonomous. Shell and arbitrary code execution
    are always high-impact because their side effects cannot be inferred
    reliably from the arguments alone.
    """
    normalized = normalize_tool_name(tool_name)
    action = str(tool_args.get("action", "")).strip().lower()

    if normalized in {"shell", "code"}:
        return "Puede ejecutar código o comandos con efectos fuera del agente."
    if normalized == "files" and action in _MUTATING_FILE_ACTIONS:
        return f"La acción de archivos '{action}' modifica el sistema de archivos."
    if normalized == "browser" and action in _MUTATING_BROWSER_ACTIONS:
        return f"La acción de navegador '{action}' puede enviar datos o cargar archivos."
    if normalized == "mcp" and action == "call_tool":
        return "Una llamada MCP puede ejecutar una acción externa no reversible."
    if action.startswith(_MUTATING_PREFIXES):
        return f"La acción externa '{action}' puede modificar recursos o enviar datos."
    return None


class ApprovalManager:
    """Store bounded, session-local approval requests with replay protection."""

    def __init__(
        self,
        ttl_seconds: float = 300.0,
        max_requests: int = 64,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if max_requests < 1:
            raise ValueError("max_requests must be at least 1")
        self._ttl_seconds = ttl_seconds
        self._max_requests = max_requests
        self._clock = clock
        self._lock = threading.RLock()
        self._requests: dict[str, ApprovalRequest] = {}

    def request_for(self, tool_name: str, tool_args: dict[str, Any]) -> Optional[ApprovalRequest]:
        """Return a pending request when a tool call needs user approval."""
        reason = approval_reason(tool_name, tool_args)
        if reason is None:
            return None
        now = self._clock()
        normalized = normalize_tool_name(tool_name)
        fingerprint = digest_stable({"tool": normalized, "args": tool_args})
        with self._lock:
            self._expire_locked(now)
            for request in self._requests.values():
                if (
                    request.status is ApprovalStatus.PENDING
                    and digest_stable({"tool": request.tool_name, "args": request.tool_args}) == fingerprint
                ):
                    return request
            self._trim_locked()
            request = ApprovalRequest(
                id=f"apr_{secrets.token_urlsafe(18)}",
                tool_name=normalized,
                tool_args=dict(tool_args),
                reason=reason,
                created_at=now,
                expires_at=now + self._ttl_seconds,
            )
            self._requests[request.id] = request
            return request

    def list_requests(self, include_finished: bool = False) -> list[dict[str, Any]]:
        """Return requests newest first without revealing any other session's data."""
        with self._lock:
            self._expire_locked(self._clock())
            requests = list(self._requests.values())
            if not include_finished:
                requests = [request for request in requests if request.status is ApprovalStatus.PENDING]
            return [request.to_public_dict() for request in reversed(requests)]

    def cancel_pending(self) -> int:
        """Cancel all pending requests when their conversation is cleared."""
        with self._lock:
            now = self._clock()
            self._expire_locked(now)
            cancelled = 0
            for request in self._requests.values():
                if request.status is ApprovalStatus.PENDING:
                    request.status = ApprovalStatus.CANCELLED
                    request.decided_at = now
                    cancelled += 1
            return cancelled

    def decide(self, request_id: str, approved: bool) -> ApprovalRequest:
        """Record one decision. Only a pending, non-expired request may change."""
        with self._lock:
            request = self._get_active_locked(request_id)
            if request.status is not ApprovalStatus.PENDING:
                raise ValueError(f"Approval request is already {request.status.value}")
            request.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.DENIED
            request.decided_at = self._clock()
            return request

    def claim_execution(self, request_id: str) -> ApprovalRequest:
        """Consume an approved request before execution, preventing replay races."""
        with self._lock:
            request = self._get_active_locked(request_id)
            if request.status is not ApprovalStatus.APPROVED:
                raise ValueError(f"Approval request is not approved (status: {request.status.value})")
            request.status = ApprovalStatus.EXECUTING
            return request

    def complete_execution(self, request_id: str, success: bool, summary: str) -> ApprovalRequest:
        """Finalize an execution after its approval has been consumed."""
        with self._lock:
            request = self._requests.get(request_id)
            if request is None:
                raise KeyError("Approval request not found")
            if request.status is not ApprovalStatus.EXECUTING:
                raise ValueError(f"Approval request is not executing (status: {request.status.value})")
            request.status = ApprovalStatus.EXECUTED
            request.result_summary = summary[:1000]
            return request

    def _get_active_locked(self, request_id: str) -> ApprovalRequest:
        self._expire_locked(self._clock())
        request = self._requests.get(request_id)
        if request is None:
            raise KeyError("Approval request not found")
        if request.status is ApprovalStatus.EXPIRED:
            raise ValueError("Approval request has expired")
        return request

    def _expire_locked(self, now: float) -> None:
        for request in self._requests.values():
            if request.status is ApprovalStatus.PENDING and request.expires_at <= now:
                request.status = ApprovalStatus.EXPIRED

    def _trim_locked(self) -> None:
        if len(self._requests) < self._max_requests:
            return
        removable = sorted(
            self._requests.values(),
            key=lambda request: request.created_at,
        )
        for request in removable:
            if request.status is not ApprovalStatus.PENDING:
                self._requests.pop(request.id, None)
                return
        raise RuntimeError("Too many pending approval requests")
