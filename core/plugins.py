"""
Plugin system for HelloChusquis.

Declarative plugin system:
- PluginManifest: declarative plugin metadata
- PluginLoader: filesystem discovery + module loading
- PluginRegistry: lifecycle management + state
- PluginHookSystem: priority-ordered hook runner
- PluginServices: service registration + dependency injection
"""

from __future__ import annotations

import importlib
import importlib.util
import json
import logging
import os
import re
import sys
import tempfile
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger("hellochusquis.plugins")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PLUGINS_DIR = Path.home() / ".hellochusquis" / "plugins"
REGISTRY_URL = "https://raw.githubusercontent.com/aminoy77/HelloChusquis-plugins/main/registry.json"
PLUGIN_MANIFEST_FILENAME = "plugin.json"
MAX_PLUGIN_MANIFEST_BYTES = 256 * 1024
_PLUGIN_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")


def validate_plugin_name(name: str) -> str:
    """Return a safe Python-module identifier for a plugin file name."""
    if not isinstance(name, str) or not _PLUGIN_NAME_RE.fullmatch(name):
        raise ValueError("Plugin name must be 1-64 letters, digits, or underscores and start with a letter")
    return name


def _secure_plugins_dir() -> None:
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(PLUGINS_DIR, 0o700)


def write_plugin_code(name: str, plugin_code: str) -> Path:
    """Atomically install trusted plugin code with owner-only permissions."""
    safe_name = validate_plugin_name(name)
    if not isinstance(plugin_code, str):
        raise ValueError("Plugin code must be text")
    _secure_plugins_dir()
    destination = PLUGINS_DIR / f"{safe_name}.py"
    descriptor, temporary_path = tempfile.mkstemp(
        prefix=f".{safe_name}.", suffix=".tmp", dir=PLUGINS_DIR
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(plugin_code)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, 0o600)
        os.replace(temporary_path, destination)
        os.chmod(destination, 0o600)
        return destination
    except Exception:
        try:
            os.unlink(temporary_path)
        except FileNotFoundError:
            pass
        raise


# Directories to skip during discovery
_SCANNED_IGNORE = frozenset({
    ".git", ".hg", ".svn", ".turbo", ".yarn", ".yarn-cache",
    "build", "coverage", "dist", "node_modules", "__pycache__",
})


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PluginStatus(str, Enum):
    DISCOVERED = "discovered"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNLOADED = "unloaded"
    ERROR = "error"


class HookFailurePolicy(str, Enum):
    FAIL_OPEN = "fail-open"
    FAIL_CLOSED = "fail-closed"


class HookType(str, Enum):
    BEFORE_TOOL_CALL = "before_tool_call"
    AFTER_TOOL_CALL = "after_tool_call"
    BEFORE_AGENT_REPLY = "before_agent_reply"
    AFTER_AGENT_REPLY = "after_agent_reply"
    ON_SESSION_START = "on_session_start"
    ON_SESSION_END = "on_session_end"
    CUSTOM = "custom"


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

@dataclass
class HookDeclaration:
    """Declares a hook a plugin implements."""
    name: str
    priority: int = 0
    tool_filter: Optional[str] = None  # None = all tools


@dataclass
class ToolDeclaration:
    """Declares a tool a plugin provides."""
    name: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class PluginManifest:
    """Declarative plugin metadata (JSON manifest)."""
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    dependencies: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    hooks: list[HookDeclaration] = field(default_factory=list)
    tools: list[ToolDeclaration] = field(default_factory=list)

    # -- helpers --

    def hook_names(self) -> list[str]:
        return [h.name for h in self.hooks]

    def tool_names(self) -> list[str]:
        return [t.name for t in self.tools]


@dataclass
class PluginRecord:
    """Runtime bookkeeping for one plugin."""
    plugin_id: str
    manifest: PluginManifest
    status: PluginStatus = PluginStatus.DISCOVERED
    module: Any = None
    root_dir: Optional[Path] = None
    source_path: Optional[Path] = None
    load_error: Optional[str] = None
    # snapshot of registration state before plugin was loaded (for rollback)
    _snapshot: Optional[dict[str, Any]] = field(default=None, repr=False)


@dataclass
class PluginCandidate:
    """Discovered plugin before manifest validation."""
    id_hint: str
    source: str
    root_dir: str
    manifest_path: Optional[str] = None


@dataclass
class PluginDiagnostic:
    """Warning or error emitted during discovery / loading."""
    level: str  # "info", "warn", "error"
    message: str
    plugin_id: Optional[str] = None
    source: Optional[str] = None


@dataclass
class HookRegistration:
    """One registered hook handler."""
    hook_name: str
    plugin_id: str
    handler: Callable[..., Any]
    priority: int = 0
    tool_filter: Optional[str] = None
    timeout_ms: Optional[int] = None


@dataclass
class ServiceRegistration:
    """One registered service."""
    service_id: str
    plugin_id: str
    factory: Callable[..., Any]
    dependencies: list[str] = field(default_factory=list)


@dataclass
class HookEvent:
    """Generic event payload passed to hook handlers."""
    data: dict[str, Any] = field(default_factory=dict)
    source: str = ""
    cancelled: bool = False
    cancel_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# PluginManifest: loading / validation
# ---------------------------------------------------------------------------

def load_manifest_from_file(path: Path) -> tuple[Optional[PluginManifest], Optional[str]]:
    """Parse plugin.json, return (manifest, error_string)."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return None, f"failed to parse manifest: {exc}"

    if not isinstance(raw, dict):
        return None, "manifest must be a JSON object"

    name = raw.get("name", "").strip()
    if not name:
        return None, "manifest requires 'name'"

    hooks = []
    for h in raw.get("hooks", []):
        if isinstance(h, dict) and "name" in h:
            hooks.append(HookDeclaration(
                name=h["name"],
                priority=int(h.get("priority", 0)),
                tool_filter=h.get("tool_filter"),
            ))

    tools = []
    for t in raw.get("tools", []):
        if isinstance(t, dict) and "name" in t:
            tools.append(ToolDeclaration(
                name=t["name"],
                description=t.get("description", ""),
                parameters=t.get("parameters", {}),
            ))

    manifest = PluginManifest(
        name=name,
        version=raw.get("version", "0.1.0"),
        description=raw.get("description", ""),
        author=raw.get("author", ""),
        dependencies=raw.get("dependencies", []),
        capabilities=raw.get("capabilities", []),
        permissions=raw.get("permissions", []),
        hooks=hooks,
        tools=tools,
    )
    return manifest, None


def load_manifest_from_module(mod: Any, module_name: str) -> tuple[Optional[PluginManifest], Optional[str]]:
    """Build manifest from legacy module attributes (PLUGIN_NAME, etc.)."""
    plugin_name = getattr(mod, "PLUGIN_NAME", None)
    if not plugin_name:
        return None, "module missing PLUGIN_NAME"

    return PluginManifest(
        name=str(plugin_name),
        version=str(getattr(mod, "PLUGIN_VERSION", "0.1.0")),
        description=str(getattr(mod, "PLUGIN_DESCRIPTION", "")),
        author=str(getattr(mod, "PLUGIN_AUTHOR", "")),
    ), None


# ---------------------------------------------------------------------------
# PluginLoader
# ---------------------------------------------------------------------------

class PluginLoader:
    """Discover and load plugins from the filesystem."""

    def __init__(self, plugins_dir: Path | None = None):
        self.plugins_dir = plugins_dir or PLUGINS_DIR
        self.diagnostics: list[PluginDiagnostic] = []
        self._loaded_modules: dict[str, Any] = {}

    # -- discovery --

    def discover(self) -> list[PluginCandidate]:
        """Scan trusted local plugin code without following unsafe filesystem links."""
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.plugins_dir, 0o700)
        candidates: list[PluginCandidate] = []
        seen: set[str] = set()

        # scan subdirectories
        for entry in sorted(self.plugins_dir.iterdir()):
            if entry.name.startswith(".") or entry.name in _SCANNED_IGNORE:
                continue
            if not self._is_trusted_entry(entry):
                continue
            if entry.is_dir():
                self._discover_directory(entry, candidates, seen)
            elif entry.is_file() and entry.suffix == ".py":
                key = str(entry.resolve())
                if key not in seen:
                    seen.add(key)
                    candidates.append(PluginCandidate(
                        id_hint=entry.stem,
                        source=str(entry),
                        root_dir=str(entry.parent),
                    ))

        logger.debug("discovered %d plugin candidate(s)", len(candidates))
        return candidates

    def _is_trusted_entry(self, entry: Path) -> bool:
        """Reject plugin paths that can escape or be modified by another local user."""
        if entry.is_symlink():
            logger.warning("Skipping symlinked plugin entry: %s", entry.name)
            return False
        try:
            mode = entry.stat().st_mode
        except OSError as exc:
            logger.warning("Skipping inaccessible plugin entry %s (%s)", entry.name, type(exc).__name__)
            return False
        if mode & 0o022:
            logger.warning("Skipping group/world-writable plugin entry: %s", entry.name)
            return False
        return True

    def _discover_directory(
        self,
        dir_path: Path,
        candidates: list[PluginCandidate],
        seen: set[str],
    ) -> None:
        manifest_path = dir_path / PLUGIN_MANIFEST_FILENAME
        init_path = dir_path / "__init__.py"
        has_manifest = manifest_path.exists() and self._is_trusted_entry(manifest_path)
        has_init = init_path.exists() and self._is_trusted_entry(init_path)

        if has_manifest:
            key = str(dir_path.resolve())
            if key in seen:
                return
            seen.add(key)
            candidates.append(PluginCandidate(
                id_hint=dir_path.name,
                source=str(dir_path / "__init__.py") if has_init else str(dir_path),
                root_dir=str(dir_path),
                manifest_path=str(manifest_path),
            ))
            return

        # recurse one level deeper for nested structures
        for sub in sorted(dir_path.iterdir()):
            if not self._is_trusted_entry(sub):
                continue
            if sub.is_dir() and sub.name not in _SCANNED_IGNORE and not sub.name.startswith("."):
                sub_manifest = sub / PLUGIN_MANIFEST_FILENAME
                sub_init = sub / "__init__.py"
                trusted_manifest = sub_manifest.exists() and self._is_trusted_entry(sub_manifest)
                trusted_init = not sub_init.exists() or self._is_trusted_entry(sub_init)
                if trusted_manifest and trusted_init:
                    key = str(sub.resolve())
                    if key not in seen:
                        seen.add(key)
                        candidates.append(PluginCandidate(
                            id_hint=sub.name,
                            source=str(sub_init) if sub_init.exists() else str(sub),
                            root_dir=str(sub),
                            manifest_path=str(sub_manifest),
                        ))

    # -- loading --

    def load_plugin(self, candidate: PluginCandidate) -> PluginRecord:
        """Load a single plugin candidate into a PluginRecord."""
        manifest: Optional[PluginManifest] = None
        module: Any = None
        error: Optional[str] = None

        # 1) Try loading manifest from plugin.json
        if candidate.manifest_path:
            mf = Path(candidate.manifest_path)
            if mf.exists():
                manifest, err = load_manifest_from_file(mf)
                if err:
                    self.diagnostics.append(PluginDiagnostic(
                        level="error", message=err,
                        plugin_id=candidate.id_hint, source=str(mf),
                    ))

        # 2) Load the Python module
        source = Path(candidate.source)
        if source.is_file() and source.suffix == ".py":
            module, err = self._load_module(source, candidate.id_hint)
        elif source.is_dir():
            init = source / "__init__.py"
            if init.exists():
                module, err = self._load_module(init, candidate.id_hint)
            else:
                error = f"directory plugin has no __init__.py: {source}"

        if err:
            error = err

        # 3) Fallback manifest from module attributes
        if manifest is None and module is not None:
            manifest, err = load_manifest_from_module(module, candidate.id_hint)
            if err:
                self.diagnostics.append(PluginDiagnostic(
                    level="warn", message=err,
                    plugin_id=candidate.id_hint, source=candidate.source,
                ))

        if manifest is None:
            manifest = PluginManifest(name=candidate.id_hint)

        status = PluginStatus.LOADED if error is None else PluginStatus.ERROR
        record = PluginRecord(
            plugin_id=manifest.name,
            manifest=manifest,
            status=status,
            module=module,
            root_dir=Path(candidate.root_dir),
            source_path=source,
            load_error=error,
        )

        if error:
            self.diagnostics.append(PluginDiagnostic(
                level="error", message=error,
                plugin_id=manifest.name, source=candidate.source,
            ))

        return record

    def _load_module(self, path: Path, plugin_id: str) -> tuple[Any, Optional[str]]:
        """Import a plugin module with isolation."""
        module_name = f"hellochusquis.plugins.{plugin_id}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                return None, f"cannot create module spec for {path}"
            mod = importlib.util.module_from_spec(spec)
            # isolate into plugins sub-namespace
            sys.modules[module_name] = mod
            spec.loader.exec_module(mod)
            self._loaded_modules[plugin_id] = mod
            return mod, None
        except Exception as exc:
            return None, f"failed to load module {path.name}: {exc}"

    # -- dependency resolution --

    def resolve_dependencies(
        self, records: list[PluginRecord],
    ) -> list[PluginRecord]:
        """Topological sort by dependencies.  Returns ordered list; errors if cycles / missing."""
        by_id: dict[str, PluginRecord] = {r.plugin_id: r for r in records}
        resolved: list[PluginRecord] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def _visit(pid: str) -> None:
            if pid in visited:
                return
            if pid in visiting:
                self.diagnostics.append(PluginDiagnostic(
                    level="error", message=f"circular dependency detected: {pid}",
                    plugin_id=pid,
                ))
                return
            rec = by_id.get(pid)
            if rec is None:
                self.diagnostics.append(PluginDiagnostic(
                    level="error", message=f"missing dependency: {pid}",
                    plugin_id=pid,
                ))
                return
            visiting.add(pid)
            for dep in rec.manifest.dependencies:
                _visit(dep)
            visiting.discard(pid)
            visited.add(pid)
            resolved.append(rec)

        for r in records:
            _visit(r.plugin_id)

        return resolved


# ---------------------------------------------------------------------------
# PluginRegistry
# ---------------------------------------------------------------------------

class PluginRegistry:
    """Central registry for plugin state, lifecycle, and metadata."""

    def __init__(self) -> None:
        self._records: dict[str, PluginRecord] = {}
        self._lock = threading.Lock()

    # -- lifecycle --

    def register(self, record: PluginRecord) -> None:
        with self._lock:
            self._records[record.plugin_id] = record
        logger.debug("registered plugin %s (status=%s)", record.plugin_id, record.status.value)

    def unregister(self, plugin_id: str) -> Optional[PluginRecord]:
        with self._lock:
            return self._records.pop(plugin_id, None)

    def enable(self, plugin_id: str) -> bool:
        with self._lock:
            rec = self._records.get(plugin_id)
            if rec is None:
                return False
            if rec.status in (PluginStatus.LOADED, PluginStatus.DISABLED):
                rec.status = PluginStatus.ENABLED
                return True
        return False

    def disable(self, plugin_id: str) -> bool:
        with self._lock:
            rec = self._records.get(plugin_id)
            if rec is None:
                return False
            if rec.status == PluginStatus.ENABLED:
                rec.status = PluginStatus.DISABLED
                return True
        return False

    def unload(self, plugin_id: str) -> bool:
        with self._lock:
            rec = self._records.get(plugin_id)
            if rec is None:
                return False
            rec.status = PluginStatus.UNLOADED
            rec.module = None
            return True

    # -- queries --

    def get(self, plugin_id: str) -> Optional[PluginRecord]:
        return self._records.get(plugin_id)

    def all_records(self) -> list[PluginRecord]:
        return list(self._records.values())

    def enabled_ids(self) -> list[str]:
        return [pid for pid, r in self._records.items() if r.status == PluginStatus.ENABLED]

    def search(self, query: str) -> list[PluginRecord]:
        q = query.lower()
        return [
            r for r in self._records.values()
            if q in r.plugin_id.lower() or q in r.manifest.name.lower()
            or q in r.manifest.description.lower()
        ]

    def count(self) -> int:
        return len(self._records)

    def to_dict(self) -> dict[str, Any]:
        return {
            pid: {
                "name": r.manifest.name,
                "version": r.manifest.version,
                "description": r.manifest.description,
                "status": r.status.value,
                "hooks": r.manifest.hook_names(),
                "tools": r.manifest.tool_names(),
            }
            for pid, r in self._records.items()
        }


# ---------------------------------------------------------------------------
# PluginHookSystem
# ---------------------------------------------------------------------------

class PluginHookSystem:
    """
    Priority-ordered hook runner.

    Supports:
      - before_tool_call / after_tool_call
      - before_agent_reply / after_agent_reply
      - on_session_start / on_session_end
      - custom hook names
    """

    def __init__(self) -> None:
        self._registrations: list[HookRegistration] = []
        self._lock = threading.Lock()
        self._failure_policy: dict[str, HookFailurePolicy] = {}

    # -- registration --

    def register_hook(
        self,
        hook_name: str,
        plugin_id: str,
        handler: Callable[..., Any],
        priority: int = 0,
        tool_filter: Optional[str] = None,
        timeout_ms: Optional[int] = None,
    ) -> None:
        reg = HookRegistration(
            hook_name=hook_name,
            plugin_id=plugin_id,
            handler=handler,
            priority=priority,
            tool_filter=tool_filter,
            timeout_ms=timeout_ms,
        )
        with self._lock:
            self._registrations.append(reg)
        logger.debug("registered hook %s from %s (priority=%d)", hook_name, plugin_id, priority)

    def unregister_hooks(self, plugin_id: str) -> int:
        with self._lock:
            before = len(self._registrations)
            self._registrations = [r for r in self._registrations if r.plugin_id != plugin_id]
            return before - len(self._registrations)

    def set_failure_policy(self, hook_name: str, policy: HookFailurePolicy) -> None:
        self._failure_policy[hook_name] = policy

    # -- retrieval (sorted by priority, highest first) --

    def _get_sorted(self, hook_name: str, tool_name: Optional[str] = None) -> list[HookRegistration]:
        with self._lock:
            regs = [r for r in self._registrations if r.hook_name == hook_name]
        if tool_name:
            regs = [r for r in regs if r.tool_filter is None or r.tool_filter == tool_name]
        regs.sort(key=lambda r: r.priority, reverse=True)
        return regs

    def hook_count(self, hook_name: str) -> int:
        return len(self._get_sorted(hook_name))

    # -- runners --

    def run_void_hook(
        self,
        hook_name: str,
        event: HookEvent,
        tool_name: Optional[str] = None,
    ) -> None:
        """Fire-and-forget: all handlers in parallel conceptually, but sequential for safety."""
        hooks = self._get_sorted(hook_name, tool_name)
        if not hooks:
            return
        logger.debug("running %s (%d handler(s))", hook_name, len(hooks))
        for reg in hooks:
            try:
                reg.handler(event, {"hook_name": hook_name, "plugin_id": reg.plugin_id})
            except Exception as exc:
                policy = self._failure_policy.get(hook_name, HookFailurePolicy.FAIL_OPEN)
                msg = f"hook {hook_name} from {reg.plugin_id} failed: {exc}"
                if policy == HookFailurePolicy.FAIL_OPEN:
                    logger.warning(msg)
                else:
                    raise RuntimeError(msg) from exc

    def run_modifying_hook(
        self,
        hook_name: str,
        event: HookEvent,
        merge_fn: Optional[Callable[[Any, Any, HookRegistration], Any]] = None,
        tool_name: Optional[str] = None,
    ) -> Any:
        """Sequential handlers; results merged. Returns accumulated result or None."""
        hooks = self._get_sorted(hook_name, tool_name)
        if not hooks:
            return None
        logger.debug("running %s (%d handler(s), modifying)", hook_name, len(hooks))
        result: Any = None
        for reg in hooks:
            try:
                handler_result = reg.handler(event, {"hook_name": hook_name, "plugin_id": reg.plugin_id})
                if handler_result is not None:
                    if merge_fn:
                        result = merge_fn(result, handler_result, reg)
                    else:
                        result = handler_result
            except Exception as exc:
                policy = self._failure_policy.get(hook_name, HookFailurePolicy.FAIL_OPEN)
                msg = f"hook {hook_name} from {reg.plugin_id} failed: {exc}"
                if policy == HookFailurePolicy.FAIL_OPEN:
                    logger.warning(msg)
                else:
                    raise RuntimeError(msg) from exc
        return result

    def run_claiming_hook(
        self,
        hook_name: str,
        event: HookEvent,
    ) -> Optional[dict[str, Any]]:
        """Sequential: first handler returning {handled: True} wins."""
        hooks = self._get_sorted(hook_name)
        if not hooks:
            return None
        logger.debug("running %s (%d handler(s), claiming)", hook_name, len(hooks))
        for reg in hooks:
            try:
                result = reg.handler(event, {"hook_name": hook_name, "plugin_id": reg.plugin_id})
                if isinstance(result, dict) and result.get("handled"):
                    return result
            except Exception as exc:
                policy = self._failure_policy.get(hook_name, HookFailurePolicy.FAIL_OPEN)
                msg = f"hook {hook_name} from {reg.plugin_id} failed: {exc}"
                if policy == HookFailurePolicy.FAIL_OPEN:
                    logger.warning(msg)
                else:
                    raise RuntimeError(msg) from exc
        return None

    # -- convenience wrappers for specific hook types --

    def run_before_tool_call(self, tool_name: str, event: HookEvent) -> Any:
        def _merge(acc: Any, nxt: Any, _reg: HookRegistration) -> Any:
            if acc is None:
                return nxt
            merged = {**acc}
            if nxt.get("block"):
                merged["block"] = True
                merged["block_reason"] = nxt.get("block_reason", merged.get("block_reason"))
            if nxt.get("params"):
                merged["params"] = nxt["params"]
            return merged

        return self.run_modifying_hook(
            HookType.BEFORE_TOOL_CALL, event, merge_fn=_merge, tool_name=tool_name,
        )

    def run_after_tool_call(self, tool_name: str, event: HookEvent) -> None:
        self.run_void_hook(HookType.AFTER_TOOL_CALL, event, tool_name=tool_name)

    def run_before_agent_reply(self, event: HookEvent) -> Optional[dict[str, Any]]:
        return self.run_claiming_hook(HookType.BEFORE_AGENT_REPLY, event)

    def run_after_agent_reply(self, event: HookEvent) -> None:
        self.run_void_hook(HookType.AFTER_AGENT_REPLY, event)

    def run_session_start(self, event: HookEvent) -> None:
        self.run_void_hook(HookType.ON_SESSION_START, event)

    def run_session_end(self, event: HookEvent) -> None:
        self.run_void_hook(HookType.ON_SESSION_END, event)


# ---------------------------------------------------------------------------
# PluginServices
# ---------------------------------------------------------------------------

class PluginServices:
    """
    Service registry: plugins register named services that can be
    discovered and injected into other plugins / host code.
    """

    def __init__(self, registry: PluginRegistry) -> None:
        self._registry = registry
        self._services: dict[str, ServiceRegistration] = {}
        self._instances: dict[str, Any] = {}
        self._lock = threading.Lock()

    # -- registration --

    def register_service(
        self,
        service_id: str,
        plugin_id: str,
        factory: Callable[..., Any],
        dependencies: list[str] | None = None,
    ) -> None:
        reg = ServiceRegistration(
            service_id=service_id,
            plugin_id=plugin_id,
            factory=factory,
            dependencies=dependencies or [],
        )
        with self._lock:
            self._services[service_id] = reg
        logger.debug("registered service %s from %s", service_id, plugin_id)

    def unregister_service(self, service_id: str) -> bool:
        with self._lock:
            removed = self._services.pop(service_id, None)
            if removed:
                self._instances.pop(service_id, None)
            return removed is not None

    # -- discovery --

    def has_service(self, service_id: str) -> bool:
        return service_id in self._services

    def list_services(self) -> list[dict[str, Any]]:
        with self._lock:
            return [
                {"id": reg.service_id, "plugin_id": reg.plugin_id, "dependencies": reg.dependencies}
                for reg in self._services.values()
            ]

    def get_service_info(self, service_id: str) -> Optional[dict[str, Any]]:
        reg = self._services.get(service_id)
        if reg is None:
            return None
        return {"id": reg.service_id, "plugin_id": reg.plugin_id, "dependencies": reg.dependencies}

    # -- dependency injection --

    def resolve(self, service_id: str, force_new: bool = False) -> Any:
        """Get or create a service instance.  Resolves dependencies transitively."""
        if not force_new and service_id in self._instances:
            return self._instances[service_id]

        reg = self._services.get(service_id)
        if reg is None:
            raise KeyError(f"service not found: {service_id}")

        # resolve dependencies first
        dep_instances: dict[str, Any] = {}
        for dep_id in reg.dependencies:
            dep_instances[dep_id] = self.resolve(dep_id)

        instance = reg.factory(**dep_instances)
        if not force_new:
            with self._lock:
                self._instances[service_id] = instance
        return instance

    def inject_all(self) -> dict[str, Any]:
        """Eagerly instantiate all registered services."""
        result: dict[str, Any] = {}
        for service_id in list(self._services.keys()):
            try:
                result[service_id] = self.resolve(service_id)
            except Exception as exc:
                logger.warning("failed to instantiate service %s: %s", service_id, exc)
        return result

    def shutdown_all(self) -> None:
        """Stop and discard all instantiated services."""
        for service_id, instance in reversed(list(self._instances.items())):
            try:
                stop_fn = getattr(instance, "stop", None)
                if callable(stop_fn):
                    stop_fn()
            except Exception as exc:
                logger.warning("error stopping service %s: %s", service_id, exc)
        with self._lock:
            self._instances.clear()


# ---------------------------------------------------------------------------
# Module-level singletons (backward compat)
# ---------------------------------------------------------------------------

_loader: Optional[PluginLoader] = None
_registry: Optional[PluginRegistry] = None
_hook_system: Optional[PluginHookSystem] = None
_services: Optional[PluginServices] = None


def _ensure_init() -> tuple[PluginLoader, PluginRegistry, PluginHookSystem, PluginServices]:
    global _loader, _registry, _hook_system, _services
    if _registry is None:
        _loader = PluginLoader()
        _registry = PluginRegistry()
        _hook_system = PluginHookSystem()
        _services = PluginServices(_registry)
    return _loader, _registry, _hook_system, _services  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# Backward-compatible public API
# ---------------------------------------------------------------------------

def init() -> None:
    """Ensure plugin directory exists with owner-only permissions."""
    _secure_plugins_dir()


def load_plugins() -> list[dict]:
    """
    Discover, load, validate, and enable plugins.
    Returns list of dicts compatible with the original API:
      {name, schema, run}
    """
    loader, registry, hook_system, _ = _ensure_init()
    init()

    candidates = loader.discover()
    records = [loader.load_plugin(c) for c in candidates]
    ordered = loader.resolve_dependencies(records)

    results: list[dict] = []
    for record in ordered:
        registry.register(record)

        if record.status == PluginStatus.ERROR:
            logger.warning("plugin %s failed to load: %s", record.plugin_id, record.load_error)
            continue

        # auto-register hooks declared in manifest
        mod = record.module
        for hook_decl in record.manifest.hooks:
            handler_name = f"on_{hook_decl.name}"
            handler = getattr(mod, handler_name, None) or getattr(mod, hook_decl.name, None)
            if callable(handler):
                hook_system.register_hook(
                    hook_name=hook_decl.name,
                    plugin_id=record.plugin_id,
                    handler=handler,
                    priority=hook_decl.priority,
                    tool_filter=hook_decl.tool_filter,
                )

        # enable
        registry.enable(record.plugin_id)

        # build legacy-compatible dict
        schema = getattr(mod, "PLUGIN_SCHEMA", {}) if mod else {}
        run_fn = getattr(mod, "run", None)
        results.append({
            "name": record.manifest.name,
            "schema": schema,
            "run": run_fn,
        })

        logger.info("loaded plugin %s v%s", record.manifest.name, record.manifest.version)

    return results


def install_plugin(name: str) -> None:
    """Download and install a plugin from the remote registry."""
    import httpx  # noqa: F811 – lazy import
    try:
        name = validate_plugin_name(name)
    except ValueError as exc:
        logger.error("Invalid plugin name: %s", exc)
        return
    init()

    try:
        with httpx.Client(timeout=30, verify=True) as client:
            r = client.get(REGISTRY_URL)
            r.raise_for_status()
            registry = r.json()
    except Exception as exc:
        logger.error("could not fetch plugin registry: %s", exc)
        return

    if name not in registry:
        logger.error("plugin '%s' not found in registry. available: %s", name, ", ".join(registry.keys()))
        return

    url = registry[name]["url"]
    try:
        with httpx.Client(timeout=30, verify=True) as client:
            r = client.get(url)
            r.raise_for_status()
            plugin_code = r.text
    except Exception as exc:
        logger.error("could not download plugin: %s", exc)
        return

    try:
        dest = write_plugin_code(name, plugin_code)
    except (OSError, ValueError) as exc:
        logger.error("could not install plugin '%s': %s", name, exc)
        return
    logger.info("plugin '%s' installed to %s", name, dest)


def list_plugins() -> None:
    """Print installed plugins."""
    init()
    installed = list(PLUGINS_DIR.glob("*.py")) + [
        d for d in PLUGINS_DIR.iterdir()
        if d.is_dir() and (d / "__init__.py").exists()
    ]
    if not installed:
        print("No plugins installed.")
        return
    print("\nInstalled plugins:")
    for p in installed:
        print(f"  ● {p.stem}")
    print()


def uninstall_plugin(name: str) -> None:
    """Remove a plugin file."""
    try:
        name = validate_plugin_name(name)
    except ValueError:
        print("✗ Invalid plugin name.")
        return
    init()
    path = PLUGINS_DIR / f"{name}.py"
    if path.exists():
        path.unlink()
        print(f"✓ Plugin '{name}' uninstalled.")
        return
    # try directory
    dir_path = PLUGINS_DIR / name
    if dir_path.is_dir():
        import shutil
        shutil.rmtree(dir_path)
        print(f"✓ Plugin '{name}' uninstalled.")
        return
    print(f"✗ Plugin '{name}' not found.")


# ---------------------------------------------------------------------------
# Public accessors for subsystems
# ---------------------------------------------------------------------------

def get_registry() -> PluginRegistry:
    _, reg, _, _ = _ensure_init()
    return reg


def get_hook_system() -> PluginHookSystem:
    _, _, hs, _ = _ensure_init()
    return hs


def get_services() -> PluginServices:
    _, _, _, sv = _ensure_init()
    return sv


def get_loader() -> PluginLoader:
    ld, _, _, _ = _ensure_init()
    return ld
