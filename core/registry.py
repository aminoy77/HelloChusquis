import asyncio
from pathlib import Path

import httpx

from core.plugins import validate_plugin_name, write_plugin_code


class PluginRegistry:
    """Manage plugin registry."""

    REGISTRY_URL = "https://raw.githubusercontent.com/aminoy77/HelloChusquis-plugins/main/registry.json"
    PLUGINS_DIR = Path.home() / ".hellochusquis" / "plugins"

    def __init__(self):
        self.local: dict = {}
        self.remote: dict = {}
        self.load_local()

    def load_local(self):
        """Load local plugins."""
        self.PLUGINS_DIR.mkdir(parents=True, exist_ok=True)
        for file in self.PLUGINS_DIR.glob("*.py"):
            name = file.stem
            self.local[name] = str(file)

    async def load_remote(self) -> dict:
        """Load remote registry."""
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(self.REGISTRY_URL, timeout=10)
                self.remote = r.json()
                return self.remote
        except Exception:
            return {}

    def install(self, name: str) -> str:
        """Install a plugin from the registry through a validated local path."""
        try:
            name = validate_plugin_name(name)
        except ValueError:
            return "Invalid plugin name"
        if name in self.local:
            return f"{name} already installed"

        if name not in self.remote:
            return f"{name} not found in registry"

        try:
            async def install_async():
                url = self.remote[name]["url"]
                async with httpx.AsyncClient() as client:
                    r = await client.get(url, timeout=30)
                    code = r.text
                    return write_plugin_code(name, code)

            path = asyncio.run(install_async())
            self.local[name] = str(path)
            return f"Installed {name} from registry"
        except Exception as e:
            return f"Failed to install: {e}"

    def uninstall(self, name: str) -> str:
        """Uninstall a plugin identified by a safe local module name."""
        try:
            name = validate_plugin_name(name)
        except ValueError:
            return "Invalid plugin name"
        if name not in self.local:
            return f"{name} not installed"

        try:
            Path(self.local[name]).unlink()
            del self.local[name]
            return f"Uninstalled {name}"
        except Exception as e:
            return f"Failed to uninstall: {e}"

    def list_all(self) -> dict:
        """List all plugins."""
        return {"installed": list(self.local.keys()), "available": list(self.remote.keys())}


def get_registry() -> PluginRegistry:
    return PluginRegistry()