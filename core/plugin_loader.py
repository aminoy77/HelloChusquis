from __future__ import annotations
import os
import importlib.util
from pathlib import Path
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class PluginInfo:
    name: str
    version: str
    description: str
    author: str
    hooks: list[str]


class PluginLoader:
    """Dynamic plugin loader for HelloChusquis."""

    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self._plugins: dict[str, Any] = {}
        self._hooks: dict[str, list[Callable]] = {}

    def discover(self) -> list[PluginInfo]:
        """Discover available plugins."""
        plugins = []
        
        if not self.plugins_dir.exists():
            return plugins

        for file in self.plugins_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
            
            try:
                spec = importlib.util.spec_from_file_location(file.stem, file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Try to get plugin info
                name = getattr(module, "PLUGIN_NAME", file.stem)
                version = getattr(module, "PLUGIN_VERSION", "1.0.0")
                description = getattr(module, "PLUGIN_DESCRIPTION", "")
                author = getattr(module, "PLUGIN_AUTHOR", "Unknown")
                hooks = getattr(module, "PLUGIN_HOOKS", [])
                
                plugins.append(PluginInfo(
                    name=name,
                    version=version,
                    description=description,
                    author=author,
                    hooks=hooks
                ))
            except Exception as e:
                print(f"Error loading {file}: {e}")

        return plugins

    def load(self, name: str) -> Any:
        """Load a specific plugin."""
        if name in self._plugins:
            return self._plugins[name]

        file = self.plugins_dir / f"{name}.py"
        if not file.exists():
            raise ValueError(f"Plugin not found: {name}")

        spec = importlib.util.spec_from_file_location(name, file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self._plugins[name] = module
        return module

    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook callback."""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)

    def trigger_hook(self, hook_name: str, *args, **kwargs):
        """Trigger all callbacks for a hook."""
        results = []
        
        for callback in self._hooks.get(hook_name, []):
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"Hook error: {e}")
        
        return results

    def create_plugin_template(self, name: str, path: str = None):
        """Create a new plugin from template."""
        path = path or str(self.plugins_dir / f"{name}.py")
        
        template = f'''"""HelloChusquis Plugin: {name}"""

PLUGIN_NAME = "{name}"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "Description of {name}"
PLUGIN_AUTHOR = "Your Name"
PLUGIN_HOOKS = ["on_message", "on_response"]

def initialize(config):
    """Initialize the plugin."""
    print(f"Initializing {{PLUGIN_NAME}}")
    return True

def on_message(message: str) -> str:
    """Hook: called when a message is received."""
    return message

def on_response(response: str) -> str:
    """Hook: called when a response is generated."""
    return response

def cleanup():
    """Cleanup when plugin is unloaded."""
    pass
'''
        
        Path(path).write_text(template)
        return path


_loader = None


def get_loader() -> PluginLoader:
    global _loader
    if _loader is None:
        _loader = PluginLoader()
    return _loader