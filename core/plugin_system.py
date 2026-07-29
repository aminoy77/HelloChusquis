from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
from typing import Any, Callable, Optional

from core.config_paths import PLUGINS_DIR, ensure_app_dirs
from core.logger import get_logger

logger = get_logger("plugin-system")

CORE_PLUGIN_API_VERSION = "1.0"
CORE_VERSION = "1.4.3"


@dataclass
class PluginManifest:
    name: str
    version: str
    description: str
    plugin_type: str  # simple | advanced
    api_version: str = CORE_PLUGIN_API_VERSION
    permissions: list[str] | None = None
    hooks: list[str] | None = None
    author: str = "Unknown"
    min_core_version: str = "1.0.0"
    max_core_version: Optional[str] = None


@dataclass
class PluginRecord:
    manifest: PluginManifest
    module: Any
    run: Callable | None
    schema: dict | None
    hooks: dict[str, Callable]


class UnifiedPluginManager:
    def __init__(self, plugins_dir: Path | None = None):
        ensure_app_dirs()
        self.plugins_dir = plugins_dir or PLUGINS_DIR
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self._loaded: dict[str, PluginRecord] = {}

    def discover_paths(self) -> list[Path]:
        return [p for p in self.plugins_dir.glob("*.py") if not p.name.startswith("_")]

    def load_all(self) -> list[dict]:
        loaded = []
        for path in self.discover_paths():
            record = self._load_path(path)
            if not record:
                continue
            loaded.append({
                "name": record.manifest.name,
                "schema": record.schema,
                "run": record.run,
                "manifest": record.manifest,
                "hooks": record.hooks,
            })
        return loaded

    def list_plugin_info(self) -> list[PluginManifest]:
        manifests: list[PluginManifest] = []
        for path in self.discover_paths():
            record = self._load_path(path)
            if record:
                manifests.append(record.manifest)
        return manifests

    def load_by_name(self, name: str) -> PluginRecord:
        if name in self._loaded:
            return self._loaded[name]
        path = self.plugins_dir / f"{name}.py"
        record = self._load_path(path)
        if not record:
            raise ValueError(f"Plugin not found or invalid: {name}")
        return record

    def _load_path(self, path: Path) -> PluginRecord | None:
        if not path.exists():
            return None
        cache_key = path.stem
        if cache_key in self._loaded:
            return self._loaded[cache_key]
        try:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            manifest = self._extract_manifest(module, path.stem)
            ok, reason = self._validate_manifest(manifest)
            if not ok:
                logger.warning("Plugin %s skipped: %s", path.name, reason)
                return None
            run_fn = getattr(module, "run", None)
            schema = getattr(module, "PLUGIN_SCHEMA", None)
            if manifest.plugin_type == "simple" and (not callable(run_fn) or not schema):
                logger.warning("Plugin %s skipped: simple plugin requires run + PLUGIN_SCHEMA", path.name)
                return None
            hooks = self._collect_hooks(module, manifest.hooks or [])
            record = PluginRecord(manifest=manifest, module=module, run=run_fn, schema=schema, hooks=hooks)
            self._loaded[manifest.name] = record
            return record
        except Exception as e:
            logger.error("Failed to load plugin %s: %s", path, e)
            return None

    def _extract_manifest(self, module: Any, fallback_name: str) -> PluginManifest:
        raw = getattr(module, "PLUGIN_MANIFEST", None)
        if isinstance(raw, dict):
            return PluginManifest(
                name=raw.get("name", fallback_name),
                version=raw.get("version", getattr(module, "PLUGIN_VERSION", "1.0.0")),
                description=raw.get("description", getattr(module, "PLUGIN_DESCRIPTION", "")),
                plugin_type=raw.get("plugin_type", "simple"),
                api_version=raw.get("api_version", CORE_PLUGIN_API_VERSION),
                permissions=list(raw.get("permissions", [])),
                hooks=list(raw.get("hooks", [])),
                author=raw.get("author", getattr(module, "PLUGIN_AUTHOR", "Unknown")),
                min_core_version=raw.get("min_core_version", "1.0.0"),
                max_core_version=raw.get("max_core_version"),
            )
        hooks = list(getattr(module, "PLUGIN_HOOKS", []))
        plugin_type = "advanced" if hooks else "simple"
        return PluginManifest(
            name=getattr(module, "PLUGIN_NAME", fallback_name),
            version=getattr(module, "PLUGIN_VERSION", "1.0.0"),
            description=getattr(module, "PLUGIN_DESCRIPTION", ""),
            plugin_type=plugin_type,
            hooks=hooks,
            author=getattr(module, "PLUGIN_AUTHOR", "Unknown"),
        )

    def _validate_manifest(self, manifest: PluginManifest) -> tuple[bool, str]:
        if manifest.plugin_type not in {"simple", "advanced"}:
            return False, "plugin_type must be simple or advanced"
        if manifest.api_version != CORE_PLUGIN_API_VERSION:
            return False, f"api_version mismatch (plugin={manifest.api_version}, core={CORE_PLUGIN_API_VERSION})"
        if not _version_ge(CORE_VERSION, manifest.min_core_version):
            return False, f"requires core >= {manifest.min_core_version}"
        if manifest.max_core_version and not _version_ge(manifest.max_core_version, CORE_VERSION):
            return False, f"requires core <= {manifest.max_core_version}"
        return True, "ok"

    def _collect_hooks(self, module: Any, hook_names: list[str]) -> dict[str, Callable]:
        hooks: dict[str, Callable] = {}
        for hook in hook_names:
            fn = getattr(module, hook, None)
            if callable(fn):
                hooks[hook] = fn
        return hooks

    def create_scaffold(self, name: str, plugin_type: str = "simple", with_tests: bool = True) -> Path:
        ensure_app_dirs()
        plugin_path = self.plugins_dir / f"{name}.py"
        if plugin_type == "advanced":
            content = _advanced_template(name)
        else:
            content = _simple_template(name)
        plugin_path.write_text(content)
        if with_tests:
            tests_dir = self.plugins_dir / "tests"
            tests_dir.mkdir(parents=True, exist_ok=True)
            test_path = tests_dir / f"test_{name}.py"
            test_path.write_text(_test_template(name))
        return plugin_path


def _version_ge(left: str, right: str) -> bool:
    def parse(v: str) -> tuple[int, int, int]:
        parts = [int(p) for p in (v.split(".") + ["0", "0"])[:3] if p.isdigit() or p.isnumeric()]
        while len(parts) < 3:
            parts.append(0)
        return tuple(parts[:3])
    return parse(left) >= parse(right)


def _simple_template(name: str) -> str:
    return f'''"""HelloChusquis plugin: {name}"""

PLUGIN_NAME = "{name}"
PLUGIN_DESCRIPTION = "Describe what this plugin does."
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "Your Name"

PLUGIN_MANIFEST = {{
    "name": "{name}",
    "version": "1.0.0",
    "description": PLUGIN_DESCRIPTION,
    "plugin_type": "simple",
    "api_version": "{CORE_PLUGIN_API_VERSION}",
    "permissions": [],
    "hooks": [],
    "min_core_version": "1.4.3"
}}

PLUGIN_SCHEMA = {{
    "type": "function",
    "function": {{
        "name": "{name}",
        "description": PLUGIN_DESCRIPTION,
        "parameters": {{
            "type": "object",
            "properties": {{
                "input": {{"type": "string", "description": "Input text"}}
            }},
            "required": ["input"]
        }}
    }}
}}

def run(input: str) -> str:
    return f"{name}: {{input}}"
'''


def _advanced_template(name: str) -> str:
    return f'''"""HelloChusquis advanced plugin: {name}"""

PLUGIN_NAME = "{name}"
PLUGIN_DESCRIPTION = "Advanced plugin with hooks."
PLUGIN_VERSION = "1.0.0"
PLUGIN_AUTHOR = "Your Name"
PLUGIN_HOOKS = ["on_message", "on_response"]

PLUGIN_MANIFEST = {{
    "name": "{name}",
    "version": "1.0.0",
    "description": PLUGIN_DESCRIPTION,
    "plugin_type": "advanced",
    "api_version": "{CORE_PLUGIN_API_VERSION}",
    "permissions": ["hooks"],
    "hooks": PLUGIN_HOOKS,
    "min_core_version": "1.4.3"
}}

def on_message(message: str) -> str:
    return message

def on_response(response: str) -> str:
    return response
'''


def _test_template(name: str) -> str:
    return f'''import importlib.util
from pathlib import Path

def test_{name}_loads():
    plugin_file = Path.home() / ".hellochusquis" / "plugins" / "{name}.py"
    spec = importlib.util.spec_from_file_location("{name}", plugin_file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "PLUGIN_MANIFEST")
'''


_manager: UnifiedPluginManager | None = None


def get_plugin_manager() -> UnifiedPluginManager:
    global _manager
    if _manager is None:
        _manager = UnifiedPluginManager()
    return _manager

