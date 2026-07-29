from __future__ import annotations

from pathlib import Path
from typing import Optional
import shutil

import yaml


APP_DIR = Path.home() / ".hellochusquis"
CANONICAL_CONFIG_PATH = APP_DIR / "config.yaml"
LOGS_DIR = APP_DIR / "logs"
PLUGINS_DIR = APP_DIR / "plugins"
WORKSPACE_DIR = APP_DIR / "workspace"


def ensure_app_dirs() -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)


def candidate_config_paths() -> list[Path]:
    return [
        CANONICAL_CONFIG_PATH,
        Path("config.yaml"),
        Path.home() / "config.yaml",
    ]


def load_config_with_migration() -> tuple[dict, Path] | tuple[None, None]:
    ensure_app_dirs()
    for path in candidate_config_paths():
        if path.exists():
            with path.open() as f:
                config = yaml.safe_load(f) or {}
            if path != CANONICAL_CONFIG_PATH:
                _migrate_config(path)
            return config, CANONICAL_CONFIG_PATH
    return None, None


def save_canonical_config(config: dict) -> Path:
    ensure_app_dirs()
    CANONICAL_CONFIG_PATH.write_text(yaml.dump(config, allow_unicode=True, sort_keys=False))
    return CANONICAL_CONFIG_PATH


def _migrate_config(source: Path) -> None:
    ensure_app_dirs()
    if source == CANONICAL_CONFIG_PATH:
        return
    shutil.copy2(source, CANONICAL_CONFIG_PATH)

