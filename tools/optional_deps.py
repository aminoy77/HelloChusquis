"""Lazy access to third-party packages that ship as optional install extras."""

from __future__ import annotations

import importlib
from types import ModuleType

# Maps an importable module name to the extra that installs it.
EXTRA_FOR_MODULE = {
    "boto3": "aws",
    "botocore": "aws",
    "speech_recognition": "voice",
    "watchdog": "watch",
}


class MissingDependencyError(RuntimeError):
    """Raised when an integration is used without its optional dependency installed."""


def require(module: str) -> ModuleType:
    """Import an optional dependency, or explain which extra provides it."""
    try:
        return importlib.import_module(module)
    except ImportError as exc:
        extra = EXTRA_FOR_MODULE.get(module.split(".")[0])
        hint = f"pip install 'hellochusquis[{extra}]'" if extra else f"pip install {module}"
        raise MissingDependencyError(
            f"'{module}' is required for this integration. Install it with: {hint}"
        ) from exc
