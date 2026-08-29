"""Multi-user identity, roles and permissions for the HTTP surfaces.

Until now a single deployment-wide API key identified *the deployment*, not a
person: anyone holding it could chat, approve high-impact actions and reload the
runtime. This module introduces named principals, each with its own secret and a
role that bounds what the principal may do.

Secrets are never stored: only their SHA-256 digest is persisted, next to a
non-secret prefix used to identify a token in listings. The legacy single key
keeps working and authenticates as a synthetic ``owner`` principal.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import threading
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

IDENTITY_DB_PATH = Path.home() / ".hellochusquis" / "identity.db"

TOKEN_PREFIX = "hc"
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
LEGACY_PRINCIPAL_NAME = "legacy-owner"


class Role(str, Enum):
    """What a principal is allowed to do, from least to most privileged."""

    VIEWER = "viewer"
    OPERATOR = "operator"
    OWNER = "owner"


class Permission(str, Enum):
    """A single authorization decision point."""

    READ_STATE = "read_state"
    CHAT = "chat"
    APPROVE = "approve"
    MUTATING_TOOLS = "mutating_tools"
    MANAGE_RUNTIME = "manage_runtime"
    MANAGE_USERS = "manage_users"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.VIEWER: frozenset({Permission.READ_STATE}),
    Role.OPERATOR: frozenset(
        {
            Permission.READ_STATE,
            Permission.CHAT,
            Permission.APPROVE,
            Permission.MUTATING_TOOLS,
        }
    ),
    Role.OWNER: frozenset(Permission),
}


class IdentityError(RuntimeError):
    """Raised when a principal cannot be created or modified."""


@dataclass(frozen=True)
class Principal:
    """An authenticated identity and the role that bounds it."""

    id: str
    name: str
    role: Role
    token_prefix: str
    created_at: str
    revoked_at: str | None = None

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None

    def has(self, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS[self.role]

    def public_view(self) -> dict:
        """A representation safe to return over HTTP: never includes a secret."""
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role.value,
            "token_prefix": self.token_prefix,
            "created_at": self.created_at,
            "revoked_at": self.revoked_at,
            "active": self.is_active,
        }


def parse_role(value: object) -> Role:
    """Convert user input into a role, rejecting anything unknown."""
    try:
        return Role(str(value or "").strip().lower())
    except ValueError as exc:
        allowed = ", ".join(role.value for role in Role)
        raise IdentityError(f"role must be one of: {allowed}") from exc


def _validate_name(value: object) -> str:
    name = str(value or "").strip().lower()
    if not _NAME_RE.fullmatch(name):
        raise IdentityError(
            "name must be 2-64 characters of lowercase letters, digits, dot, dash or underscore."
        )
    return name


def _token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class IdentityStore:
    """Persist principals with owner-only file permissions."""

    def __init__(self, db_path: Path | str = IDENTITY_DB_PATH) -> None:
        self._db_path = db_path
        self._lock = threading.RLock()
        self._conn = self._connect(db_path)
        self._create_schema()

    @staticmethod
    def _connect(db_path: Path | str) -> sqlite3.Connection:
        file_backed = str(db_path) != ":memory:"
        if file_backed:
            db_path = Path(db_path)
            db_path.parent.mkdir(parents=True, exist_ok=True)
            managed_directory = Path.home() / ".hellochusquis"
            if db_path.parent == managed_directory:
                os.chmod(managed_directory, 0o700)
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        if file_backed:
            os.chmod(db_path, 0o600)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS principals (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    role TEXT NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    token_prefix TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    revoked_at TEXT
                )
                """
            )
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    # -- mutations ---------------------------------------------------------

    def create(self, name: str, role: Role | str) -> tuple[Principal, str]:
        """Create a principal and return it with its one-time plaintext token."""
        clean_name = _validate_name(name)
        clean_role = role if isinstance(role, Role) else parse_role(role)
        principal_id = secrets.token_hex(8)
        secret = secrets.token_urlsafe(32)
        token = f"{TOKEN_PREFIX}_{principal_id}_{secret}"
        created_at = _now()
        with self._lock:
            try:
                self._conn.execute(
                    "INSERT INTO principals (id, name, role, token_hash, token_prefix, created_at)"
                    " VALUES (?, ?, ?, ?, ?, ?)",
                    (principal_id, clean_name, clean_role.value, _token_digest(token), principal_id, created_at),
                )
                self._conn.commit()
            except sqlite3.IntegrityError as exc:
                raise IdentityError(f"a principal named '{clean_name}' already exists") from exc
        principal = Principal(
            id=principal_id,
            name=clean_name,
            role=clean_role,
            token_prefix=principal_id,
            created_at=created_at,
        )
        return principal, token

    def revoke(self, name: str) -> Principal:
        """Revoke a principal's token; authentication fails from then on."""
        clean_name = _validate_name(name)
        with self._lock:
            existing = self.get_by_name(clean_name)
            if existing is None:
                raise IdentityError(f"no principal named '{clean_name}'")
            if not existing.is_active:
                return existing
            if existing.role is Role.OWNER and self._active_owner_count() <= 1:
                raise IdentityError("cannot revoke the last active owner")
            revoked_at = _now()
            self._conn.execute(
                "UPDATE principals SET revoked_at = ? WHERE name = ?", (revoked_at, clean_name)
            )
            self._conn.commit()
            return replace(existing, revoked_at=revoked_at)

    def _active_owner_count(self) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS total FROM principals WHERE role = ? AND revoked_at IS NULL",
            (Role.OWNER.value,),
        ).fetchone()
        return int(row["total"])

    # -- queries -----------------------------------------------------------

    @staticmethod
    def _row_to_principal(row: sqlite3.Row) -> Principal:
        return Principal(
            id=row["id"],
            name=row["name"],
            role=Role(row["role"]),
            token_prefix=row["token_prefix"],
            created_at=row["created_at"],
            revoked_at=row["revoked_at"],
        )

    def get_by_name(self, name: str) -> Principal | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM principals WHERE name = ?", (str(name).strip().lower(),)
            ).fetchone()
        return self._row_to_principal(row) if row else None

    def list_principals(self) -> list[Principal]:
        with self._lock:
            rows = self._conn.execute("SELECT * FROM principals ORDER BY created_at").fetchall()
        return [self._row_to_principal(row) for row in rows]

    def authenticate(self, token: str) -> Principal | None:
        """Resolve a bearer token to an active principal, or ``None``.

        The lookup is by digest, so no secret is compared in plaintext and no
        secret is ever read back out of the database.
        """
        candidate = str(token or "")
        if not candidate:
            return None
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM principals WHERE token_hash = ? AND revoked_at IS NULL",
                (_token_digest(candidate),),
            ).fetchone()
        return self._row_to_principal(row) if row else None


_default_store: IdentityStore | None = None
_default_store_lock = threading.Lock()


def default_store() -> IdentityStore:
    """Open the process-wide store lazily so an import creates no database."""
    global _default_store
    with _default_store_lock:
        if _default_store is None:
            _default_store = IdentityStore(os.environ.get("HELLOCHUSQUIS_IDENTITY_DB") or IDENTITY_DB_PATH)
        return _default_store


def reset_default_store() -> None:
    """Drop the cached store; used by tests that repoint the database."""
    global _default_store
    with _default_store_lock:
        if _default_store is not None:
            _default_store.close()
        _default_store = None


def authenticate_bearer(token: str, legacy_key: str | None = None) -> Principal | None:
    """Resolve a bearer token, accepting the deployment-wide key as an owner.

    Keeping the legacy key valid means adding identities never locks an
    existing deployment out of its own HTTP surface.
    """
    candidate = str(token or "")
    if legacy_key and hmac.compare_digest(candidate, legacy_key):
        return legacy_owner()
    try:
        return default_store().authenticate(candidate)
    except Exception:  # A storage failure must not authenticate anyone.
        return None


def legacy_owner(token_prefix: str = "legacy") -> Principal:
    """The synthetic principal used when the deployment-wide key authenticates."""
    return Principal(
        id="legacy",
        name=LEGACY_PRINCIPAL_NAME,
        role=Role.OWNER,
        token_prefix=token_prefix,
        created_at="",
    )
