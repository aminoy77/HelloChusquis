"""Local marketplace catalog and installers."""

from __future__ import annotations

import json
import os
import re
import shutil
import ast
from pathlib import Path
from typing import Any


ITEM_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")
DEFAULT_HOME = Path.home() / ".hellochusquis"
SKILLS_DIR = DEFAULT_HOME / "skills"
PLUGINS_DIR = DEFAULT_HOME / "plugins"
MCP_CONFIG = DEFAULT_HOME / "mcp.json"
CATALOG_FILE = Path(__file__).with_name("marketplace_catalog.json")


class MarketplaceError(ValueError):
    pass


def _safe_id(value: Any) -> str:
    item_id = str(value or "").strip()
    if not ITEM_ID_RE.fullmatch(item_id):
        raise MarketplaceError("Invalid marketplace item id")
    return item_id


def load_catalog() -> list[dict[str, Any]]:
    try:
        data = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MarketplaceError(f"Unable to read marketplace catalog: {exc}") from exc
    items = data.get("items") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise MarketplaceError("Marketplace catalog has invalid format")
    catalog = [item for item in items if isinstance(item, dict)]
    known_ids = {str(item.get("id")) for item in catalog}

    tools_dir = CATALOG_FILE.resolve().parents[1] / "tools"
    for source in sorted(tox_path for tox_path in tools_dir.glob("*.py") if tox_path.name not in {"__init__.py"}):
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        plugin_name = ""
        description = ""
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            value = node.value
            if not isinstance(value, ast.Constant) or not isinstance(value.value, str):
                continue
            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue
                if target.id == "PLUGIN_NAME":
                    plugin_name = value.value
                elif target.id == "PLUGIN_DESCRIPTION":
                    description = value.value
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", plugin_name) or plugin_name in known_ids:
            continue
        catalog.append({
            "id": plugin_name,
            "kind": "plugin",
            "name": plugin_name.replace("_", " ").replace("-", " ").title(),
            "description": description or f"Local {plugin_name} integration plugin.",
            "source": source.stem,
        })
        known_ids.add(plugin_name)

    skills_dir = CATALOG_FILE.resolve().parents[1] / "examples" / "skills"
    if skills_dir.is_dir():
        for skill_file in sorted(skills_dir.glob("*/SKILL.md")):
            skill_id = skill_file.parent.name
            if skill_id in known_ids:
                continue
            body = skill_file.read_text(encoding="utf-8")
            match = re.search(r"^description:\s*(.+)$", body, re.MULTILINE)
            catalog.append({
                "id": skill_id,
                "kind": "skill",
                "name": skill_id.replace("-", " ").replace("_", " ").title(),
                "description": match.group(1).strip() if match else "Local HelloChusquis skill.",
                "skill_md": body,
            })
            known_ids.add(skill_id)

    return catalog


def get_item(item_id: str) -> dict[str, Any]:
    safe_id = _safe_id(item_id)
    for item in load_catalog():
        if item.get("id") == safe_id:
            return item
    raise MarketplaceError(f"Unknown marketplace item: {safe_id}")


def list_items(kind: str = "") -> list[dict[str, Any]]:
    kind = kind.strip().lower()
    return [
        item
        for item in load_catalog()
        if not kind or item.get("kind") == kind
    ]


def is_installed(item: dict[str, Any]) -> bool:
    item_id = _safe_id(item["id"])
    kind = item.get("kind")
    if kind == "skill":
        return (SKILLS_DIR / item_id / "SKILL.md").is_file()
    if kind == "plugin":
        return (PLUGINS_DIR / f"{item_id}.py").is_file()
    if kind == "mcp":
        try:
            data = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return False
        return item_id in data.get("mcpServers", {}) if isinstance(data, dict) else False
    return False


def _atomic_write(path: Path, content: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def install_item(item_id: str) -> dict[str, Any]:
    item = get_item(item_id)
    kind = item.get("kind")
    item_id = _safe_id(item["id"])

    if kind == "skill":
        body = item.get("skill_md")
        if not isinstance(body, str) or not body.strip():
            raise MarketplaceError("Skill package is missing SKILL.md content")
        destination = SKILLS_DIR / item_id / "SKILL.md"
        _atomic_write(destination, body)
    elif kind == "plugin":
        source_name = item.get("source")
        if not isinstance(source_name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]{0,63}", source_name):
            raise MarketplaceError("Plugin package has an invalid source")
        source = Path(__file__).resolve().parents[1] / "tools" / f"{source_name}.py"
        if not source.is_file():
            raise MarketplaceError(f"Bundled plugin source is missing: {source_name}")
        PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(PLUGINS_DIR, 0o700)
        destination = PLUGINS_DIR / f"{item_id}.py"
        shutil.copyfile(source, destination)
        os.chmod(destination, 0o600)
    elif kind == "mcp":
        config = item.get("config")
        if not isinstance(config, dict):
            raise MarketplaceError("MCP package has invalid configuration")
        try:
            existing = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
        except FileNotFoundError:
            existing = {}
        except json.JSONDecodeError as exc:
            raise MarketplaceError(f"MCP configuration is invalid: {exc}") from exc
        if not isinstance(existing, dict):
            raise MarketplaceError("MCP configuration root must be a JSON object")
        servers = existing.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            raise MarketplaceError("MCP mcpServers entry must be a JSON object")
        servers[item_id] = config
        _atomic_write(MCP_CONFIG, json.dumps(existing, indent=2, ensure_ascii=False) + "\n")
    else:
        raise MarketplaceError(f"Unsupported marketplace item kind: {kind}")
    return {"status": "installed", "item": item_id, "kind": kind}


def uninstall_item(item_id: str) -> dict[str, Any]:
    item = get_item(item_id)
    kind = item.get("kind")
    item_id = _safe_id(item["id"])

    if kind == "skill":
        destination = SKILLS_DIR / item_id
        if destination.is_dir():
            shutil.rmtree(destination)
    elif kind == "plugin":
        destination = PLUGINS_DIR / f"{item_id}.py"
        destination.unlink(missing_ok=True)
    elif kind == "mcp":
        try:
            existing = json.loads(MCP_CONFIG.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            existing = {}
        if isinstance(existing, dict):
            servers = existing.get("mcpServers")
            if isinstance(servers, dict):
                servers.pop(item_id, None)
                _atomic_write(MCP_CONFIG, json.dumps(existing, indent=2, ensure_ascii=False) + "\n")
    else:
        raise MarketplaceError(f"Unsupported marketplace item kind: {kind}")
    return {"status": "uninstalled", "item": item_id, "kind": kind}
