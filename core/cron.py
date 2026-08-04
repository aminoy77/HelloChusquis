"""
Cron scheduling system for HelloChusquis.

Provides:
  - CronSchedule: cron expression parsing, interval-based schedules, next-run computation
  - CronJob: full lifecycle, retry logic, delivery, heartbeat monitoring, metadata
  - CronService: timer management, persistence, pacing, failure alerting, stats
  - CronDelivery: multi-target delivery with retry
  - CronScheduler: backward-compatible facade
"""

from __future__ import annotations

import json
import logging
import math
import os
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional, Protocol

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DAY_S = 86_400
_HOUR_S = 3_600
_MINUTE_S = 60
_MAX_RETRY_BACKOFF_S = 3_600  # 1 hour cap
_DEFAULT_MAX_RETRIES = 3
_DEFAULT_BACKOFF_BASE_S = 5.0
_DEFAULT_PACING_MIN_INTERVAL_S = 60.0
_DEFAULT_STUCK_THRESHOLD_S = 1_800  # 30 minutes
_DEFAULT_FAILURE_ALERT_COOLDOWN_S = 300.0
_FAILURE_NOTIFICATION_TIMEOUT_S = 30.0

# Cron field ranges (standard cron)
_CRON_RANGES: dict[str, tuple[int, int]] = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day": (1, 31),
    "month": (1, 12),
    "weekday": (0, 7),  # 0 and 7 = Sunday
}

_MONTH_NAMES: dict[str, int] = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}

_WEEKDAY_NAMES: dict[str, int] = {
    "SUN": 0, "MON": 1, "TUE": 2, "WED": 3, "THU": 4, "FRI": 5, "SAT": 6,
}


# ---------------------------------------------------------------------------
# Cron expression parser
# ---------------------------------------------------------------------------

def _parse_iso(s: str) -> Optional[datetime]:
    """Parse ISO-8601 datetime string to timezone-aware datetime."""
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _expand_cron_field(field_str: str, lo: int, hi: int, names: Optional[dict[str, int]] = None) -> list[int]:
    """Expand a single cron field into a sorted list of valid values.

    Supports: *, */N, N, N-M, N-M/S, comma-separated values, and named
    months/weekdays.
    """
    values: set[int] = set()
    for part in field_str.split(","):
        part = part.strip()
        if part == "*":
            values.update(range(lo, hi + 1))
            continue
        # Step: */N or N-M/S
        step = 1
        step_match = re.match(r"^(.+)/(\d+)$", part)
        if step_match:
            part = step_match.group(1)
            step = int(step_match.group(2))
            if step <= 0:
                raise ValueError(f"Step must be positive: {part}")
        # After step extraction, part may still be "*"
        if part == "*":
            values.update(range(lo, hi + 1, step))
            continue
        # Range: N-M
        if "-" in part:
            pieces = part.split("-", 1)
            start_s, end_s = pieces
            start = _resolve_named(start_s, names, lo)
            end = _resolve_named(end_s, names, lo)
            for v in range(start, end + 1, step):
                if lo <= v <= hi:
                    values.add(v)
        else:
            v = _resolve_named(part, names, lo)
            if lo <= v <= hi:
                values.add(v)
    if not values:
        raise ValueError(f"No valid values in cron field: {field_str!r}")
    return sorted(values)


def _resolve_named(s: str, names: Optional[dict[str, int]], lo: int) -> int:
    """Resolve a named value (e.g. JAN, MON) to int, or parse int directly."""
    if names:
        upper = s.upper()
        if upper in names:
            # For weekday: map 7 -> 0 (Sunday)
            val = names[upper]
            if val == 7 and lo == 0:
                return 0
            return val
    return int(s)


def _validate_cron_field(field_str: str, name: str) -> None:
    """Validate a single cron field without expanding it."""
    lo, hi = _CRON_RANGES[name]
    for part in field_str.split(","):
        part = part.strip()
        step_match = re.match(r"^(.+)/(\d+)$", part)
        if step_match:
            part = step_match.group(1)
        if part == "*":
            continue
        if "-" in part:
            pieces = part.split("-", 1)
            _validate_cron_atom(pieces[0], name, lo, hi)
            _validate_cron_atom(pieces[1], name, lo, hi)
        else:
            _validate_cron_atom(part, name, lo, hi)


def _validate_cron_atom(s: str, name: str, lo: int, hi: int) -> None:
    """Validate one atom (number or name) within a cron field."""
    upper = s.upper()
    if _MONTH_NAMES and upper in _MONTH_NAMES:
        v = _MONTH_NAMES[upper]
    elif _WEEKDAY_NAMES and upper in _WEEKDAY_NAMES:
        v = _WEEKDAY_NAMES[upper]
        if v == 7 and lo == 0:
            v = 0
    else:
        v = int(s)
    if not (lo <= v <= hi):
        raise ValueError(f"Cron field {name}: value {v} out of range [{lo}-{hi}]")


def _cron_matches_for_day(
    expr: str, day_dt: datetime, tz: Optional[str] = None
) -> list[datetime]:
    """Return all matching datetimes for a given cron expression on a given day."""
    parts = expr.strip().split()
    if len(parts) != 5:
        return []

    minutes = _expand_cron_field(parts[0], 0, 59)
    hours = _expand_cron_field(parts[1], 0, 23)
    # For day/month we expand for range-checking but filter below
    day_vals = _expand_cron_field(parts[2], 1, 31)
    month_vals = _expand_cron_field(parts[3], 1, 12)
    weekday_vals = _expand_cron_field(parts[4], 0, 7)

    matches: list[datetime] = []

    if day_dt.month not in month_vals:
        return []

    # Check weekday: cron weekday 7 == 0 == Sunday
    wd = day_dt.weekday()  # 0=Mon..6=Sun
    cron_wd = (wd + 1) % 7  # Convert to 0=Sun..6=Sat
    # Normalize: if weekday_vals has 7, treat as 0
    norm_weekday = set(weekday_vals)
    if 7 in norm_weekday:
        norm_weekday.add(0)
    if cron_wd not in norm_weekday:
        return []

    if day_dt.day not in day_vals:
        return []

    for h in hours:
        for m in minutes:
            dt = day_dt.replace(hour=h, minute=m, second=0, microsecond=0)
            if dt.timestamp() > time.time() - _DAY_S:
                matches.append(dt)

    return sorted(matches)


def _previous_cron_match(
    expr: str, tz: Optional[str], now_s: float
) -> Optional[float]:
    """Find the most recent cron match before now_s."""
    now_dt = datetime.fromtimestamp(now_s, tz=timezone.utc)
    for day_offset in range(0, 367):
        base = now_dt - timedelta(days=day_offset)
        candidates = _cron_matches_for_day(expr, base, tz)
        for cand in reversed(candidates):
            cand_s = cand.timestamp()
            if cand_s < now_s:
                return cand_s
    return None


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ScheduleKind(str, Enum):
    AT = "at"
    EVERY = "every"
    CRON = "cron"


class DeliveryMode(str, Enum):
    NONE = "none"
    ANNOUNCE = "announce"
    WEBHOOK = "webhook"
    CHANNEL = "channel"


class DeliveryStatus(str, Enum):
    DELIVERED = "delivered"
    NOT_DELIVERED = "not-delivered"
    UNKNOWN = "unknown"
    NOT_REQUESTED = "not-requested"


class RunStatus(str, Enum):
    OK = "ok"
    ERROR = "error"
    SKIPPED = "skipped"


# ---------------------------------------------------------------------------
# CronSchedule
# ---------------------------------------------------------------------------

@dataclass
class CronSchedule:
    """Schedule specification supporting cron expressions, intervals, and one-shot times.

    Usage::

        # Cron expression
        CronSchedule.cron("*/5 * * * *")                     # every 5 minutes
        CronSchedule.cron("0 9 * * 1-5", tz="US/Eastern")   # 9am weekdays ET

        # Interval-based
        CronSchedule.every(seconds=300)  # every 5 minutes

        # One-shot
        CronSchedule.at("2026-08-04T10:00:00Z")
    """

    kind: ScheduleKind
    expr: Optional[str] = None
    tz: Optional[str] = None
    every_s: Optional[float] = None
    anchor_s: Optional[float] = None
    at_iso: Optional[str] = None
    stagger_s: float = 0.0

    # -- Factory methods ----------------------------------------------------

    @classmethod
    def cron(cls, expr: str, tz: Optional[str] = None, stagger_s: float = 0.0) -> CronSchedule:
        """Parse and validate a standard 5-field cron expression."""
        cls._validate_cron_expr(expr)
        return cls(kind=ScheduleKind.CRON, expr=expr.strip(), tz=tz, stagger_s=stagger_s)

    @classmethod
    def every(cls, seconds: float, anchor_s: Optional[float] = None) -> CronSchedule:
        """Interval-based schedule."""
        if seconds <= 0:
            raise ValueError(f"Interval must be positive, got {seconds}")
        return cls(
            kind=ScheduleKind.EVERY,
            every_s=max(1.0, math.floor(seconds)),
            anchor_s=anchor_s,
        )

    @classmethod
    def at(cls, iso_datetime: str) -> CronSchedule:
        """One-shot schedule at an ISO-8601 datetime."""
        dt = _parse_iso(iso_datetime)
        if dt is None:
            raise ValueError(f"Invalid ISO-8601 datetime: {iso_datetime}")
        return cls(kind=ScheduleKind.AT, at_iso=iso_datetime)

    # -- Validation ---------------------------------------------------------

    @staticmethod
    def _validate_cron_expr(expr: str) -> None:
        """Validate a 5-field cron expression."""
        parts = expr.strip().split()
        if len(parts) != 5:
            raise ValueError(
                f"Cron expression must have 5 fields (minute hour day month weekday), "
                f"got {len(parts)}: {expr!r}"
            )
        field_names = ["minute", "hour", "day", "month", "weekday"]
        for part, name in zip(parts, field_names):
            _validate_cron_field(part, name)

    # -- Next run computation -----------------------------------------------

    def next_run_after(self, now_s: float) -> Optional[float]:
        """Compute the next run timestamp (epoch seconds) after *now_s*."""
        if self.kind == ScheduleKind.AT:
            return self._next_at(now_s)
        if self.kind == ScheduleKind.EVERY:
            return self._next_every(now_s)
        if self.kind == ScheduleKind.CRON:
            return self._next_cron(now_s)
        return None

    def previous_run_before(self, now_s: float) -> Optional[float]:
        """Compute the most recent cron run timestamp before *now_s* (cron only)."""
        if self.kind != ScheduleKind.CRON or not self.expr:
            return None
        return _previous_cron_match(self.expr, self.tz, now_s)

    def validate(self) -> None:
        """Raise if schedule is invalid."""
        if self.kind == ScheduleKind.CRON:
            if not self.expr:
                raise ValueError("Cron schedule requires an expr")
            self._validate_cron_expr(self.expr)
        elif self.kind == ScheduleKind.EVERY:
            if not self.every_s or self.every_s <= 0:
                raise ValueError("Interval schedule requires positive every_s")
        elif self.kind == ScheduleKind.AT:
            if not self.at_iso:
                raise ValueError("At-schedule requires at_iso")

    # -- Private helpers ----------------------------------------------------

    def _next_at(self, now_s: float) -> Optional[float]:
        if not self.at_iso:
            return None
        dt = _parse_iso(self.at_iso)
        if dt is None:
            return None
        ts = dt.timestamp()
        return ts if ts > now_s else None

    def _next_every(self, now_s: float) -> Optional[float]:
        every = max(1.0, math.floor(self.every_s or 1.0))
        anchor = max(0.0, math.floor(self.anchor_s if self.anchor_s is not None else now_s))
        if now_s < anchor:
            return anchor
        elapsed = now_s - anchor
        steps = math.floor(elapsed / every) + 1
        return anchor + steps * every

    def _next_cron(self, now_s: float) -> Optional[float]:
        if not self.expr:
            return None
        now_dt = datetime.fromtimestamp(now_s, tz=timezone.utc)
        for day_offset in range(0, 367):
            base = now_dt + timedelta(days=day_offset)
            candidates = _cron_matches_for_day(self.expr, base, self.tz)
            for cand in candidates:
                cand_s = cand.timestamp()
                if cand_s > now_s:
                    if self.stagger_s > 0:
                        h = hash(self.expr or "") % int(self.stagger_s * 1000)
                        cand_s += h / 1000.0
                    return cand_s
        return None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"kind": self.kind.value}
        if self.expr is not None:
            d["expr"] = self.expr
        if self.tz is not None:
            d["tz"] = self.tz
        if self.every_s is not None:
            d["every_s"] = self.every_s
        if self.anchor_s is not None:
            d["anchor_s"] = self.anchor_s
        if self.at_iso is not None:
            d["at_iso"] = self.at_iso
        if self.stagger_s:
            d["stagger_s"] = self.stagger_s
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CronSchedule:
        kind = ScheduleKind(d.get("kind", "every"))
        return cls(
            kind=kind,
            expr=d.get("expr"),
            tz=d.get("tz"),
            every_s=d.get("every_s"),
            anchor_s=d.get("anchor_s"),
            at_iso=d.get("at_iso"),
            stagger_s=d.get("stagger_s", 0.0),
        )


# ---------------------------------------------------------------------------
# DeliveryTarget
# ---------------------------------------------------------------------------

@dataclass
class DeliveryTarget:
    """Target for cron job output delivery."""

    mode: DeliveryMode = DeliveryMode.NONE
    channel: Optional[str] = None
    to: Optional[str] = None
    thread_id: Optional[str | int] = None
    account_id: Optional[str] = None
    webhook_url: Optional[str] = None
    best_effort: bool = False

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"mode": self.mode.value}
        if self.channel:
            d["channel"] = self.channel
        if self.to:
            d["to"] = self.to
        if self.thread_id is not None:
            d["thread_id"] = self.thread_id
        if self.account_id:
            d["account_id"] = self.account_id
        if self.webhook_url:
            d["webhook_url"] = self.webhook_url
        if self.best_effort:
            d["best_effort"] = True
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> DeliveryTarget:
        return cls(
            mode=DeliveryMode(d.get("mode", "none")),
            channel=d.get("channel"),
            to=d.get("to"),
            thread_id=d.get("thread_id"),
            account_id=d.get("account_id"),
            webhook_url=d.get("webhook_url"),
            best_effort=d.get("best_effort", False),
        )


# ---------------------------------------------------------------------------
# FailureAlert
# ---------------------------------------------------------------------------

@dataclass
class FailureAlert:
    """Configuration for failure alerting after consecutive errors."""

    after: int = 3
    channel: Optional[str] = None
    to: Optional[str] = None
    cooldown_s: float = _DEFAULT_FAILURE_ALERT_COOLDOWN_S
    include_skipped: bool = False
    mode: Optional[str] = None
    account_id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"after": self.after}
        if self.channel:
            d["channel"] = self.channel
        if self.to:
            d["to"] = self.to
        if self.cooldown_s != _DEFAULT_FAILURE_ALERT_COOLDOWN_S:
            d["cooldown_s"] = self.cooldown_s
        if self.include_skipped:
            d["include_skipped"] = True
        if self.mode:
            d["mode"] = self.mode
        if self.account_id:
            d["account_id"] = self.account_id
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FailureAlert:
        return cls(
            after=d.get("after", 3),
            channel=d.get("channel"),
            to=d.get("to"),
            cooldown_s=d.get("cooldown_s", _DEFAULT_FAILURE_ALERT_COOLDOWN_S),
            include_skipped=d.get("include_skipped", False),
            mode=d.get("mode"),
            account_id=d.get("account_id"),
        )


# ---------------------------------------------------------------------------
# CronRunResult
# ---------------------------------------------------------------------------

@dataclass
class CronRunResult:
    """Result of a single cron job execution."""

    status: RunStatus = RunStatus.OK
    error: Optional[str] = None
    summary: Optional[str] = None
    output: Optional[str] = None
    duration_s: float = 0.0
    delivered: bool = False
    delivery_status: DeliveryStatus = DeliveryStatus.NOT_REQUESTED
    delivery_error: Optional[str] = None
    session_id: Optional[str] = None
    timestamp_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "status": self.status.value,
            "duration_s": self.duration_s,
            "delivered": self.delivered,
            "delivery_status": self.delivery_status.value,
            "timestamp_s": self.timestamp_s,
        }
        if self.error:
            d["error"] = self.error
        if self.summary:
            d["summary"] = self.summary
        if self.output:
            d["output"] = self.output
        if self.delivery_error:
            d["delivery_error"] = self.delivery_error
        if self.session_id:
            d["session_id"] = self.session_id
        return d


# ---------------------------------------------------------------------------
# CronJobState
# ---------------------------------------------------------------------------

@dataclass
class CronJobState:
    """Mutable runtime state persisted beside the immutable job spec."""

    next_run_at_s: Optional[float] = None
    last_run_at_s: Optional[float] = None
    last_run_status: Optional[RunStatus] = None
    last_error: Optional[str] = None
    last_duration_s: Optional[float] = None
    consecutive_errors: int = 0
    consecutive_skipped: int = 0
    last_failure_alert_at_s: Optional[float] = None
    running_at_s: Optional[float] = None
    scheduled_run_count: int = 0
    completed_run_count: int = 0
    failed_run_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "consecutive_errors": self.consecutive_errors,
            "consecutive_skipped": self.consecutive_skipped,
            "scheduled_run_count": self.scheduled_run_count,
            "completed_run_count": self.completed_run_count,
            "failed_run_count": self.failed_run_count,
        }
        if self.next_run_at_s is not None:
            d["next_run_at_s"] = self.next_run_at_s
        if self.last_run_at_s is not None:
            d["last_run_at_s"] = self.last_run_at_s
        if self.last_run_status is not None:
            d["last_run_status"] = self.last_run_status.value
        if self.last_error:
            d["last_error"] = self.last_error
        if self.last_duration_s is not None:
            d["last_duration_s"] = self.last_duration_s
        if self.last_failure_alert_at_s is not None:
            d["last_failure_alert_at_s"] = self.last_failure_alert_at_s
        if self.running_at_s is not None:
            d["running_at_s"] = self.running_at_s
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CronJobState:
        status_raw = d.get("last_run_status")
        return cls(
            next_run_at_s=d.get("next_run_at_s"),
            last_run_at_s=d.get("last_run_at_s"),
            last_run_status=RunStatus(status_raw) if status_raw else None,
            last_error=d.get("last_error"),
            last_duration_s=d.get("last_duration_s"),
            consecutive_errors=d.get("consecutive_errors", 0),
            consecutive_skipped=d.get("consecutive_skipped", 0),
            last_failure_alert_at_s=d.get("last_failure_alert_at_s"),
            running_at_s=d.get("running_at_s"),
            scheduled_run_count=d.get("scheduled_run_count", 0),
            completed_run_count=d.get("completed_run_count", 0),
            failed_run_count=d.get("failed_run_count", 0),
        )


# ---------------------------------------------------------------------------
# CronJob
# ---------------------------------------------------------------------------

@dataclass
class CronJob:
    """A scheduled job with full lifecycle, retry, delivery, and metadata.

    Lifecycle::

        PENDING -> RUNNING -> COMPLETED / FAILED
        Any -> PAUSED
        PAUSED -> PENDING (resume)

    Retry on failure with exponential backoff up to max_retries.
    """

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = ""
    action: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    schedule: CronSchedule = field(default_factory=lambda: CronSchedule.every(seconds=3600))
    status: JobStatus = JobStatus.PENDING
    enabled: bool = True

    # Retry
    max_retries: int = _DEFAULT_MAX_RETRIES
    backoff_base_s: float = _DEFAULT_BACKOFF_BASE_S
    backoff_max_s: float = _MAX_RETRY_BACKOFF_S

    # Delivery
    delivery: DeliveryTarget = field(default_factory=DeliveryTarget)
    failure_alert: Optional[FailureAlert] = None

    # Pacing
    pacing_min_interval_s: float = _DEFAULT_PACING_MIN_INTERVAL_S

    # Heartbeat / stuck detection
    heartbeat_timeout_s: float = _DEFAULT_STUCK_THRESHOLD_S

    # Metadata
    tags: dict[str, str] = field(default_factory=dict)
    declaration_key: Optional[str] = None
    display_name: Optional[str] = None
    agent_id: Optional[str] = None
    session_target: str = "main"  # "main" | "isolated" | "current"
    wake_mode: str = "next-heartbeat"  # "next-heartbeat" | "now"
    owner_agent_id: Optional[str] = None

    # Timestamps
    created_at_s: float = field(default_factory=time.time)
    updated_at_s: float = field(default_factory=time.time)

    # Mutable state
    state: CronJobState = field(default_factory=CronJobState)

    # Run history (last N results)
    run_history: list[CronRunResult] = field(default_factory=list)
    _max_history: int = field(default=50, repr=False)

    # -- Lifecycle ----------------------------------------------------------

    def mark_running(self) -> None:
        """Transition to RUNNING state."""
        if self.status == JobStatus.PAUSED:
            raise RuntimeError(f"Job {self.id} is paused, cannot run")
        self.status = JobStatus.RUNNING
        self.state.running_at_s = time.time()
        self.updated_at_s = time.time()

    def mark_completed(self, result: CronRunResult) -> None:
        """Transition to COMPLETED and record result."""
        self.status = JobStatus.COMPLETED
        self.state.last_run_at_s = time.time()
        self.state.last_run_status = RunStatus.OK
        self.state.last_duration_s = result.duration_s
        self.state.consecutive_errors = 0
        self.state.consecutive_skipped = 0
        self.state.completed_run_count += 1
        self.state.running_at_s = None
        self.updated_at_s = time.time()
        self._record_run(result)

    def mark_failed(self, result: CronRunResult) -> None:
        """Transition to FAILED with retry tracking."""
        self.status = JobStatus.FAILED
        self.state.last_run_at_s = time.time()
        self.state.last_run_status = RunStatus.ERROR
        self.state.last_error = result.error
        self.state.last_duration_s = result.duration_s
        self.state.consecutive_errors += 1
        self.state.consecutive_skipped = 0
        self.state.failed_run_count += 1
        self.state.running_at_s = None
        self.updated_at_s = time.time()
        self._record_run(result)

    def mark_skipped(self) -> None:
        """Record a skipped execution."""
        self.state.consecutive_skipped += 1
        self.state.last_run_status = RunStatus.SKIPPED
        self.state.running_at_s = None
        self.updated_at_s = time.time()

    def pause(self) -> None:
        """Pause job scheduling."""
        self.status = JobStatus.PAUSED
        self.updated_at_s = time.time()

    def resume(self) -> None:
        """Resume job scheduling."""
        if self.status == JobStatus.PAUSED:
            self.status = JobStatus.PENDING
            self.updated_at_s = time.time()

    def reset_consecutive_errors(self) -> None:
        """Reset the consecutive error counter."""
        self.state.consecutive_errors = 0
        self.updated_at_s = time.time()

    # -- Scheduling helpers -------------------------------------------------

    def should_run(self, now_s: Optional[float] = None) -> bool:
        """Check if the job is due to run."""
        now_s = now_s or time.time()
        if not self.enabled:
            return False
        if self.status == JobStatus.PAUSED:
            return False
        if self.status == JobStatus.RUNNING:
            return False
        # Pacing: respect minimum interval
        if self.state.last_run_at_s is not None:
            elapsed = now_s - self.state.last_run_at_s
            if elapsed < self.pacing_min_interval_s:
                return False
        # Check schedule
        return self.schedule.next_run_after(now_s) is not None

    def next_run(self, now_s: Optional[float] = None) -> Optional[float]:
        """Get the next scheduled run time."""
        now_s = now_s or time.time()
        return self.schedule.next_run_after(now_s)

    def retry_delay_s(self) -> float:
        """Compute exponential backoff delay for current retry count."""
        errors = self.state.consecutive_errors
        if errors <= 0:
            return 0.0
        delay = self.backoff_base_s * (2 ** (errors - 1))
        return min(delay, self.backoff_max_s)

    def should_retry(self) -> bool:
        """Check if the job should be retried after failure."""
        return self.state.consecutive_errors < self.max_retries

    def is_stuck(self, now_s: Optional[float] = None) -> bool:
        """Check if the job is stuck (running longer than heartbeat timeout)."""
        if self.status != JobStatus.RUNNING:
            return False
        if self.state.running_at_s is None:
            return False
        now_s = now_s or time.time()
        return (now_s - self.state.running_at_s) > self.heartbeat_timeout_s

    def should_alert_failure(self, now_s: Optional[float] = None) -> bool:
        """Check if a failure alert should be sent."""
        if not self.failure_alert:
            return False
        now_s = now_s or time.time()
        threshold = self.failure_alert.after
        count = self.state.consecutive_errors
        if self.failure_alert.include_skipped:
            count += self.state.consecutive_skipped
        if count < threshold:
            return False
        if self.state.last_failure_alert_at_s is not None:
            since = now_s - self.state.last_failure_alert_at_s
            if since < self.failure_alert.cooldown_s:
                return False
        return True

    def record_failure_alert_sent(self, now_s: Optional[float] = None) -> None:
        """Record that a failure alert was sent."""
        self.state.last_failure_alert_at_s = now_s or time.time()
        self.updated_at_s = time.time()

    # -- History ------------------------------------------------------------

    def _record_run(self, result: CronRunResult) -> None:
        self.run_history.append(result)
        if len(self.run_history) > self._max_history:
            self.run_history = self.run_history[-self._max_history:]

    def last_n_results(self, n: int = 10) -> list[CronRunResult]:
        """Get the last N run results."""
        return self.run_history[-n:]

    def success_rate(self) -> float:
        """Compute success rate (0.0 - 1.0)."""
        total = self.state.completed_run_count + self.state.failed_run_count
        if total == 0:
            return 1.0
        return self.state.completed_run_count / total

    # -- Serialization ------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "action": self.action,
            "params": self.params,
            "schedule": self.schedule.to_dict(),
            "status": self.status.value,
            "enabled": self.enabled,
            "max_retries": self.max_retries,
            "backoff_base_s": self.backoff_base_s,
            "backoff_max_s": self.backoff_max_s,
            "delivery": self.delivery.to_dict(),
            "failure_alert": self.failure_alert.to_dict() if self.failure_alert else None,
            "pacing_min_interval_s": self.pacing_min_interval_s,
            "heartbeat_timeout_s": self.heartbeat_timeout_s,
            "tags": self.tags,
            "declaration_key": self.declaration_key,
            "display_name": self.display_name,
            "agent_id": self.agent_id,
            "session_target": self.session_target,
            "wake_mode": self.wake_mode,
            "owner_agent_id": self.owner_agent_id,
            "created_at_s": self.created_at_s,
            "updated_at_s": self.updated_at_s,
            "state": self.state.to_dict(),
            "run_history": [r.to_dict() for r in self.run_history[-self._max_history:]],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> CronJob:
        schedule_data = d.get("schedule", {})
        delivery_data = d.get("delivery", {})
        failure_data = d.get("failure_alert")
        state_data = d.get("state", {})
        history_data = d.get("run_history", [])

        job = cls(
            id=d.get("id", uuid.uuid4().hex[:12]),
            name=d.get("name", ""),
            action=d.get("action", ""),
            params=d.get("params", {}),
            schedule=CronSchedule.from_dict(schedule_data) if schedule_data else CronSchedule.every(seconds=3600),
            status=JobStatus(d.get("status", "pending")),
            enabled=d.get("enabled", True),
            max_retries=d.get("max_retries", _DEFAULT_MAX_RETRIES),
            backoff_base_s=d.get("backoff_base_s", _DEFAULT_BACKOFF_BASE_S),
            backoff_max_s=d.get("backoff_max_s", _MAX_RETRY_BACKOFF_S),
            delivery=DeliveryTarget.from_dict(delivery_data) if delivery_data else DeliveryTarget(),
            failure_alert=FailureAlert.from_dict(failure_data) if failure_data else None,
            pacing_min_interval_s=d.get("pacing_min_interval_s", _DEFAULT_PACING_MIN_INTERVAL_S),
            heartbeat_timeout_s=d.get("heartbeat_timeout_s", _DEFAULT_STUCK_THRESHOLD_S),
            tags=d.get("tags", {}),
            declaration_key=d.get("declaration_key"),
            display_name=d.get("display_name"),
            agent_id=d.get("agent_id"),
            session_target=d.get("session_target", "main"),
            wake_mode=d.get("wake_mode", "next-heartbeat"),
            owner_agent_id=d.get("owner_agent_id"),
            created_at_s=d.get("created_at_s", time.time()),
            updated_at_s=d.get("updated_at_s", time.time()),
            state=CronJobState.from_dict(state_data),
        )
        for rd in history_data:
            job.run_history.append(CronRunResult(
                status=RunStatus(rd.get("status", "ok")),
                error=rd.get("error"),
                summary=rd.get("summary"),
                output=rd.get("output"),
                duration_s=rd.get("duration_s", 0.0),
                delivered=rd.get("delivered", False),
                delivery_status=DeliveryStatus(rd.get("delivery_status", "not-requested")),
                delivery_error=rd.get("delivery_error"),
                session_id=rd.get("session_id"),
                timestamp_s=rd.get("timestamp_s", 0.0),
            ))
        return job


# ---------------------------------------------------------------------------
# CronDelivery
# ---------------------------------------------------------------------------

class CronDelivery:
    """Delivers cron job results to configured targets.

    Supports:
      - Channel delivery (announce to messaging channel)
      - Webhook delivery (HTTP POST)
      - Failure notifications with cooldown
      - Delivery retry on transient failures
    """

    def __init__(self, max_retries: int = 3, retry_delay_s: float = 5.0) -> None:
        self.max_retries = max_retries
        self.retry_delay_s = retry_delay_s

    def deliver(
        self,
        job: CronJob,
        result: CronRunResult,
        message: Optional[str] = None,
    ) -> bool:
        """Deliver job result to configured target.

        Returns True if delivery succeeded or was not requested.
        """
        target = job.delivery
        if target.mode == DeliveryMode.NONE:
            result.delivery_status = DeliveryStatus.NOT_REQUESTED
            return True

        message = message or self._format_message(job, result)

        for attempt in range(1, self.max_retries + 1):
            try:
                if target.mode in (DeliveryMode.CHANNEL, DeliveryMode.ANNOUNCE):
                    ok = self._deliver_channel(target, message)
                elif target.mode == DeliveryMode.WEBHOOK:
                    ok = self._deliver_webhook(target, job, result, message)
                else:
                    ok = False

                if ok:
                    result.delivered = True
                    result.delivery_status = DeliveryStatus.DELIVERED
                    return True

            except Exception as exc:
                logger.warning("Delivery attempt %d failed for job %s: %s", attempt, job.id, exc)
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay_s * attempt)

        result.delivery_status = DeliveryStatus.NOT_DELIVERED
        result.delivery_error = f"All {self.max_retries} delivery attempts failed"
        return False

    def send_failure_notification(
        self,
        job: CronJob,
        error_message: str,
    ) -> bool:
        """Send a best-effort failure notification with bounded timeout."""
        if not job.failure_alert:
            return False

        target = DeliveryTarget(
            mode=DeliveryMode.ANNOUNCE,
            channel=job.failure_alert.channel,
            to=job.failure_alert.to,
            account_id=job.failure_alert.account_id,
            best_effort=True,
        )

        text = (
            f"[Cron Failure] Job '{job.name}' ({job.id})\n"
            f"Consecutive errors: {job.state.consecutive_errors}\n"
            f"Error: {error_message}"
        )

        deadline = time.time() + _FAILURE_NOTIFICATION_TIMEOUT_S
        for attempt in range(1, 4):
            if time.time() >= deadline:
                break
            try:
                if target.mode == DeliveryMode.ANNOUNCE and target.channel:
                    ok = self._deliver_channel(target, text)
                    if ok:
                        job.record_failure_alert_sent()
                        return True
            except Exception as exc:
                logger.debug("Failure notification attempt %d failed: %s", attempt, exc)
                if attempt < 3:
                    time.sleep(1.0)

        logger.warning("Failed to send failure notification for job %s", job.id)
        return False

    @staticmethod
    def _format_message(job: CronJob, result: CronRunResult) -> str:
        """Format a delivery message from job and result."""
        parts = [f"[Cron] {job.display_name or job.name} ({job.id})"]
        if result.summary:
            parts.append(result.summary)
        if result.output:
            output = result.output[:2000]
            if len(result.output) > 2000:
                output += "..."
            parts.append(output)
        if result.status == RunStatus.ERROR and result.error:
            parts.append(f"Error: {result.error}")
        parts.append(f"Duration: {result.duration_s:.1f}s")
        return "\n".join(parts)

    @staticmethod
    def _deliver_channel(target: DeliveryTarget, message: str) -> bool:
        """Deliver to a messaging channel (hook point for service integration)."""
        logger.info(
            "Channel delivery: channel=%s to=%s thread=%s",
            target.channel, target.to, target.thread_id,
        )
        return True

    @staticmethod
    def _deliver_webhook(
        target: DeliveryTarget,
        job: CronJob,
        result: CronRunResult,
        message: str,
    ) -> bool:
        """Deliver to a webhook endpoint via HTTP POST."""
        import urllib.request
        import urllib.error

        url = target.webhook_url
        if not url:
            logger.warning("Webhook delivery requested but no URL for job %s", job.id)
            return False

        payload = json.dumps({
            "job_id": job.id,
            "job_name": job.name,
            "status": result.status.value,
            "message": message,
            "summary": result.summary,
            "error": result.error,
            "timestamp": result.timestamp_s,
            "tags": job.tags,
        }).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                return 200 <= resp.status < 300
        except (urllib.error.URLError, OSError) as exc:
            logger.warning("Webhook delivery failed for job %s: %s", job.id, exc)
            return False


# ---------------------------------------------------------------------------
# CronStats
# ---------------------------------------------------------------------------

@dataclass
class CronStats:
    """Aggregate statistics for the cron service."""

    total_jobs: int = 0
    enabled_jobs: int = 0
    running_jobs: int = 0
    failed_jobs: int = 0
    paused_jobs: int = 0
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    last_tick_s: Optional[float] = None
    uptime_s: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_jobs": self.total_jobs,
            "enabled_jobs": self.enabled_jobs,
            "running_jobs": self.running_jobs,
            "failed_jobs": self.failed_jobs,
            "paused_jobs": self.paused_jobs,
            "total_runs": self.total_runs,
            "successful_runs": self.successful_runs,
            "failed_runs": self.failed_runs,
            "last_tick_s": self.last_tick_s,
            "uptime_s": self.uptime_s,
        }


# ---------------------------------------------------------------------------
# AgentExecutor protocol
# ---------------------------------------------------------------------------

class AgentExecutor(Protocol):
    """Protocol for agents that can execute cron job actions."""

    def run(self, action: str, params: dict[str, Any]) -> Any: ...


# ---------------------------------------------------------------------------
# CronService
# ---------------------------------------------------------------------------

class CronService:
    """Full cron scheduling service with persistence, pacing, heartbeat
    monitoring, and failure alerting.
    """

    def __init__(
        self,
        store_path: Optional[str | Path] = None,
        executor: Optional[AgentExecutor] = None,
        delivery: Optional[CronDelivery] = None,
        missed_stagger_s: float = 1.0,
        max_missed_per_restart: int = 10,
    ) -> None:
        self._jobs: dict[str, CronJob] = {}
        self._store_path = Path(
            store_path or os.path.join(str(Path.home()), ".hellochusquis", "cron.json")
        )
        self._executor = executor
        self._delivery = delivery or CronDelivery()
        self._missed_stagger_s = missed_stagger_s
        self._max_missed_per_restart = max_missed_per_restart

        # Timer state
        self._running = False
        self._stopped = False
        self._scheduling_paused = False
        self._scheduler_started = False
        self._timer: Optional[threading.Timer] = None
        self._tick_interval_s: float = 10.0
        self._lock = threading.Lock()

        # Stats
        self._stats = CronStats()
        self._started_at_s: float = 0.0

        # Events
        self._event_listeners: list[Callable[..., None]] = []

        # Load persisted jobs
        self._load()

    # -- Public API ---------------------------------------------------------

    def add(
        self,
        name: str,
        interval: Optional[float] = None,
        action: str = "",
        params: Optional[dict[str, Any]] = None,
        cron_expr: Optional[str] = None,
        tz: Optional[str] = None,
        at_iso: Optional[str] = None,
        **kwargs: Any,
    ) -> CronJob:
        """Add a new cron job. Supports interval, cron expression, or one-shot schedule."""
        if cron_expr:
            schedule = CronSchedule.cron(cron_expr, tz=tz)
        elif at_iso:
            schedule = CronSchedule.at(at_iso)
        elif interval is not None:
            schedule = CronSchedule.every(seconds=interval)
        else:
            schedule = CronSchedule.every(seconds=3600)

        # Extract known CronJob fields from kwargs
        known_fields = {
            "id", "max_retries", "backoff_base_s", "backoff_max_s",
            "delivery", "failure_alert", "pacing_min_interval_s",
            "heartbeat_timeout_s", "tags", "declaration_key", "display_name",
            "agent_id", "session_target", "wake_mode", "owner_agent_id", "enabled",
        }
        extra = {k: v for k, v in kwargs.items() if k in known_fields}

        job = CronJob(
            name=name,
            action=action,
            params=params or {},
            schedule=schedule,
            **extra,
        )

        job.state.next_run_at_s = job.schedule.next_run_after(time.time())

        with self._lock:
            self._jobs[job.id] = job
        self._emit("added", job=job)
        self._save()
        return job

    def remove(self, job_id: str) -> bool:
        """Remove a job by ID."""
        with self._lock:
            job = self._jobs.pop(job_id, None)
        if job is None:
            return False
        self._emit("removed", job=job)
        self._save()
        return True

    def get(self, job_id: str) -> Optional[CronJob]:
        """Get a job by ID."""
        return self._jobs.get(job_id)

    def get_by_name(self, name: str) -> Optional[CronJob]:
        """Get the first job matching a name."""
        for job in self._jobs.values():
            if job.name == name:
                return job
        return None

    def list_jobs(
        self,
        include_disabled: bool = False,
        include_paused: bool = True,
    ) -> list[CronJob]:
        """List all jobs with optional filters."""
        result = []
        for job in self._jobs.values():
            if not include_disabled and not job.enabled:
                continue
            if not include_paused and job.status == JobStatus.PAUSED:
                continue
            result.append(job)
        return sorted(result, key=lambda j: j.name)

    def get_pending(self) -> list[CronJob]:
        """Get jobs that are due to run now."""
        now = time.time()
        return [job for job in self._jobs.values() if job.should_run(now)]

    def pause(self, job_id: str) -> bool:
        """Pause a job."""
        job = self._jobs.get(job_id)
        if job is None:
            return False
        job.pause()
        self._emit("updated", job=job)
        self._save()
        return True

    def resume(self, job_id: str) -> bool:
        """Resume a paused job."""
        job = self._jobs.get(job_id)
        if job is None:
            return False
        job.resume()
        job.state.next_run_at_s = job.schedule.next_run_after(time.time())
        self._emit("updated", job=job)
        self._save()
        return True

    def run_job(self, job_id: str, force: bool = False) -> Optional[CronRunResult]:
        """Run a specific job immediately.

        Args:
            job_id: The job to run.
            force: If True, bypass pacing and scheduling checks.
        """
        job = self._jobs.get(job_id)
        if job is None:
            logger.warning("Job %s not found", job_id)
            return None

        if job.status == JobStatus.RUNNING:
            logger.info("Job %s already running, skipping", job_id)
            return None

        if not force and not job.should_run():
            logger.info("Job %s not due, skipping", job_id)
            return None

        return self._execute_job(job)

    def run_pending(self, agent: Optional[AgentExecutor] = None) -> list[str]:
        """Run all pending jobs. Backward-compatible with CronScheduler interface."""
        executor = agent or self._executor
        results: list[str] = []

        for job in self.get_pending():
            old_executor = self._executor
            if executor:
                self._executor = executor
            result = self._execute_job(job)
            if executor:
                self._executor = old_executor

            if result:
                if result.status == RunStatus.OK:
                    results.append(f"{job.name}: {result.summary or 'ok'}")
                else:
                    results.append(f"{job.name}: Error - {result.error}")
            else:
                results.append(f"{job.name}: Skipped")

        return results

    # -- Timer management ---------------------------------------------------

    def start(self, tick_interval_s: float = 10.0) -> None:
        """Start the cron service scheduler loop."""
        if self._running:
            logger.debug("CronService already running")
            return
        self._running = True
        self._stopped = False
        self._scheduling_paused = False
        self._tick_interval_s = tick_interval_s
        self._started_at_s = time.time()
        self._scheduler_started = True
        self._schedule_next_tick(tick_interval_s)
        logger.info("CronService started (tick=%.1fs)", tick_interval_s)

    def stop(self) -> None:
        """Stop the cron service scheduler loop."""
        self._stopped = True
        self._running = False
        self._scheduler_started = False
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None
        logger.info("CronService stopped")

    def pause_scheduling(self) -> None:
        """Pause scheduling without stopping the service."""
        self._scheduling_paused = True
        logger.info("CronService scheduling paused")

    def resume_scheduling(self) -> None:
        """Resume scheduling after pause."""
        self._scheduling_paused = False
        logger.info("CronService scheduling resumed")

    def stop_and_drain(self) -> None:
        """Stop and persist final state."""
        self.stop()
        self._save()

    # -- Status & events ----------------------------------------------------

    def status(self) -> dict[str, Any]:
        """Get service status summary."""
        self._update_stats()
        return {
            "enabled": self._running and not self._stopped,
            "store_path": str(self._store_path),
            "jobs": len(self._jobs),
            "scheduler_started": self._scheduler_started,
            "scheduling_paused": self._scheduling_paused,
            "stats": self._stats.to_dict(),
        }

    def on_event(self, listener: Callable[..., None]) -> None:
        """Register an event listener."""
        self._event_listeners.append(listener)

    def remove_event_listener(self, listener: Callable[..., None]) -> None:
        """Remove an event listener."""
        self._event_listeners = [l for l in self._event_listeners if l is not listener]

    # -- Heartbeat monitoring -----------------------------------------------

    def check_stuck_jobs(self) -> list[CronJob]:
        """Check for stuck jobs and return them."""
        stuck: list[CronJob] = []
        for job in self._jobs.values():
            if job.is_stuck():
                stuck.append(job)
                logger.warning(
                    "Job %s (%s) stuck: running since %.0fs (timeout=%.0fs)",
                    job.id, job.name,
                    time.time() - (job.state.running_at_s or 0),
                    job.heartbeat_timeout_s,
                )
                # Reset stuck job to pending for retry
                job.status = JobStatus.FAILED
                job.state.running_at_s = None
                result = CronRunResult(
                    status=RunStatus.ERROR,
                    error="Job stuck (heartbeat timeout exceeded)",
                    timestamp_s=time.time(),
                )
                job._record_run(result)
                if job.should_retry():
                    job.state.consecutive_errors += 1
                    job.status = JobStatus.PENDING
                    job.state.next_run_at_s = time.time() + job.retry_delay_s()
        if stuck:
            self._save()
        return stuck

    def get_heartbeat_monitor_specs(
        self,
        agent_ids: list[str],
        interval_s: float = 1800.0,
    ) -> list[dict[str, Any]]:
        """Resolve heartbeat monitor job specs for given agents.
        """
        specs: list[dict[str, Any]] = []
        for agent_id in agent_ids:
            declaration_key = f"heartbeat:{agent_id}"
            # Skip if already exists
            existing = self.get_by_declaration_key(declaration_key)
            if existing:
                continue
            specs.append({
                "declaration_key": declaration_key,
                "display_name": f"Heartbeat ({agent_id})",
                "name": f"heartbeat-{agent_id}",
                "agent_id": agent_id,
                "schedule": {"kind": "every", "every_s": interval_s},
                "payload_kind": "heartbeat",
                "session_target": "main",
                "wake_mode": "next-heartbeat",
            })
        return specs

    def get_by_declaration_key(self, key: str) -> Optional[CronJob]:
        """Get a job by its declaration key."""
        for job in self._jobs.values():
            if job.declaration_key == key:
                return job
        return None

    def remove_stale_job_family(
        self,
        declaration_key: str,
        owner_agent_id: str,
    ) -> int:
        """Remove all jobs in a family (by declaration key prefix + owner)."""
        to_remove: list[str] = []
        for job in self._jobs.values():
            if (
                job.declaration_key
                and job.declaration_key.startswith(declaration_key)
                and job.owner_agent_id == owner_agent_id
            ):
                to_remove.append(job.id)
        for jid in to_remove:
            self._jobs.pop(jid, None)
        if to_remove:
            self._save()
        return len(to_remove)

    # -- Stats --------------------------------------------------------------

    def get_stats(self) -> CronStats:
        """Get aggregate statistics."""
        self._update_stats()
        return self._stats

    def get_job_history(self, job_id: str, limit: int = 20) -> list[CronRunResult]:
        """Get run history for a specific job."""
        job = self._jobs.get(job_id)
        if job is None:
            return []
        return job.last_n_results(limit)

    # -- Internal execution -------------------------------------------------

    def _execute_job(self, job: CronJob) -> Optional[CronRunResult]:
        """Execute a single job with retry, delivery, and heartbeat support."""
        now = time.time()

        # Check retry backoff
        if job.state.consecutive_errors > 0 and job.should_retry():
            delay = job.retry_delay_s()
            next_retry = (job.state.last_run_at_s or 0) + delay
            if now < next_retry:
                return None  # Still in backoff

        job.mark_running()
        self._emit("started", job=job, run_at_ms=now)

        result = CronRunResult(timestamp_s=now)
        start_time = time.time()

        try:
            if self._executor is not None:
                output = self._executor.run(job.action, job.params)
                result.output = str(output) if output is not None else None
                result.summary = result.output[:200] if result.output else "completed"
                result.status = RunStatus.OK
            else:
                result.output = f"No executor configured for action: {job.action}"
                result.summary = "No executor"
                result.status = RunStatus.SKIPPED
        except Exception as exc:
            result.status = RunStatus.ERROR
            result.error = str(exc)
            logger.error("Job %s (%s) failed: %s", job.id, job.name, exc)

        result.duration_s = time.time() - start_time
        result.timestamp_s = time.time()

        # Update job state
        if result.status == RunStatus.OK:
            job.mark_completed(result)
        elif result.status == RunStatus.ERROR:
            job.mark_failed(result)
        else:
            job.mark_skipped()

        # Compute next run
        job.state.next_run_at_s = job.schedule.next_run_after(time.time())

        # Delivery
        if result.status in (RunStatus.OK, RunStatus.ERROR):
            self._delivery.deliver(job, result)

        # Failure alerting
        if result.status == RunStatus.ERROR and job.should_alert_failure():
            alert_sent = self._delivery.send_failure_notification(job, result.error or "Unknown error")
            if alert_sent:
                job.record_failure_alert_sent()

        # Persist and emit
        self._save()
        self._emit(
            "finished",
            job=job,
            run_at_ms=start_time,
            duration_ms=result.duration_s * 1000,
            status=result.status,
            error=result.error,
            summary=result.summary,
            delivered=result.delivered,
        )

        return result

    # -- Timer tick ---------------------------------------------------------

    def _schedule_next_tick(self, interval_s: float) -> None:
        """Schedule the next timer tick."""
        if self._timer is not None:
            self._timer.cancel()
        if self._running and not self._stopped:
            self._timer = threading.Timer(interval_s, self._tick)
            self._timer.daemon = True
            self._timer.start()

    def _tick(self) -> None:
        """Timer tick: check for due jobs, stuck jobs, failure alerts."""
        if self._stopped or not self._running:
            return

        now = time.time()

        if not self._scheduling_paused:
            # Check stuck jobs
            self.check_stuck_jobs()

            # Run due jobs
            pending = self.get_pending()
            for job in pending:
                if job.status != JobStatus.PAUSED and job.enabled:
                    try:
                        self._execute_job(job)
                    except Exception as exc:
                        logger.error("Error executing job %s: %s", job.id, exc)

        # Update stats
        self._stats.last_tick_s = now
        self._stats.uptime_s = now - self._started_at_s if self._started_at_s else 0

        # Schedule next tick
        self._schedule_next_tick(self._tick_interval_s)

    # -- Persistence --------------------------------------------------------

    def _save(self) -> None:
        """Persist jobs to JSON file."""
        with self._lock:
            store = {
                "version": 1,
                "jobs": [j.to_dict() for j in self._jobs.values()],
            }
        try:
            self._store_path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._store_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(store, indent=2))
            tmp.replace(self._store_path)
        except OSError as exc:
            logger.error("Failed to persist cron store: %s", exc)

    def _load(self) -> None:
        """Load jobs from JSON file."""
        if not self._store_path.exists():
            return
        try:
            data = json.loads(self._store_path.read_text())
            version = data.get("version", 1)
            jobs_data = data.get("jobs", []) if version == 1 else data if isinstance(data, list) else []

            for jd in jobs_data:
                try:
                    job = CronJob.from_dict(jd)
                    self._jobs[job.id] = job
                except Exception as exc:
                    logger.warning("Failed to load cron job: %s", exc)

            # Recover missed jobs on startup
            now = time.time()
            missed = 0
            for job in self._jobs.values():
                if not job.enabled or job.status == JobStatus.PAUSED:
                    continue
                next_s = job.state.next_run_at_s
                if next_s is not None and next_s < now:
                    missed += 1
                    if missed <= self._max_missed_per_restart:
                        # Run immediately
                        job.state.next_run_at_s = now
                    else:
                        # Stagger replay
                        stagger = (missed - self._max_missed_per_restart) * self._missed_stagger_s
                        job.state.next_run_at_s = now + stagger

            if missed:
                logger.info(
                    "CronService recovered %d missed jobs (%d immediate, %d staggered)",
                    missed,
                    min(missed, self._max_missed_per_restart),
                    max(0, missed - self._max_missed_per_restart),
                )

        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Failed to load cron store from %s: %s", self._store_path, exc)

    # -- Events -------------------------------------------------------------

    def _emit(self, action: str, **kwargs: Any) -> None:
        """Emit a lifecycle event to registered listeners."""
        event = {"action": action, **kwargs}
        for listener in self._event_listeners:
            try:
                listener(event)
            except Exception:
                pass  # Never let listener errors break scheduler

    # -- Stats update -------------------------------------------------------

    def _update_stats(self) -> None:
        """Recompute aggregate statistics."""
        s = self._stats
        s.total_jobs = len(self._jobs)
        s.enabled_jobs = sum(1 for j in self._jobs.values() if j.enabled)
        s.running_jobs = sum(1 for j in self._jobs.values() if j.status == JobStatus.RUNNING)
        s.failed_jobs = sum(1 for j in self._jobs.values() if j.status == JobStatus.FAILED)
        s.paused_jobs = sum(1 for j in self._jobs.values() if j.status == JobStatus.PAUSED)
        s.total_runs = sum(j.state.completed_run_count + j.state.failed_run_count for j in self._jobs.values())
        s.successful_runs = sum(j.state.completed_run_count for j in self._jobs.values())
        s.failed_runs = sum(j.state.failed_run_count for j in self._jobs.values())
        if self._started_at_s:
            s.uptime_s = time.time() - self._started_at_s

    # -- Backward compat: save/load on explicit path ------------------------

    def save(self) -> None:
        """Public save (backward compat with CronScheduler)."""
        self._save()

    def load(self) -> None:
        """Public load (backward compat with CronScheduler)."""
        self._load()


# ---------------------------------------------------------------------------
# CronScheduler: backward-compatible facade
# ---------------------------------------------------------------------------

class CronScheduler:
    """Manage scheduled tasks. Backward-compatible interface with enhanced features.

    Supports the original CronScheduler.add/remove/get_pending/run_pending API
    plus full CronService capabilities.
    """

    def __init__(self, store_path: Optional[str | Path] = None) -> None:
        self._service = CronService(store_path=store_path)
        self.jobs: list[CronJob] = []  # Legacy attribute for backward compat

    @property
    def service(self) -> CronService:
        """Access the underlying CronService."""
        return self._service

    def add(self, name: str, interval: int, action: str, params: dict = None) -> CronJob:
        """Add a job. Backward-compatible with original CronScheduler.add().

        For advanced scheduling, use service.add() with cron_expr or at_iso.
        """
        job = self._service.add(
            name=name,
            interval=float(interval),
            action=action,
            params=params or {},
        )
        self._sync_jobs_list()
        return job

    def remove(self, name: str) -> None:
        """Remove jobs by name. Backward-compatible."""
        to_remove = [j for j in self._service.list_jobs(include_disabled=True, include_paused=True) if j.name == name]
        for job in to_remove:
            self._service.remove(job.id)
        self._sync_jobs_list()

    def get_pending(self) -> list[CronJob]:
        """Get jobs due to run. Backward-compatible."""
        return self._service.get_pending()

    def run_pending(self, agent) -> list[str]:
        """Run all pending jobs. Backward-compatible with original interface."""
        self._service._executor = agent
        results = self._service.run_pending()
        self._sync_jobs_list()
        return results

    def save(self) -> None:
        """Persist jobs. Backward-compatible."""
        self._service.save()

    def load(self) -> None:
        """Load persisted jobs. Backward-compatible."""
        self._service.load()
        self._sync_jobs_list()

    def _sync_jobs_list(self) -> None:
        """Sync the legacy jobs list attribute."""
        self.jobs = self._service.list_jobs(include_disabled=True, include_paused=True)


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_scheduler_instance: Optional[CronScheduler] = None


def get_scheduler() -> CronScheduler:
    """Get or create the global CronScheduler singleton. Backward-compatible."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = CronScheduler()
    return _scheduler_instance
