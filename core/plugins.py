import importlib.util
import sys
from pathlib import Path
from rich.console import Console

console = Console()
PLUGINS_DIR = Path.home() / ".hellochusquis" / "plugins"
REGISTRY_URL = "https://raw.githubusercontent.com/aminoy77/HelloChusquis-plugins/main/registry.json"


def init():
    PLUGINS_DIR.mkdir(parents=True, exist_ok=True)


def load_plugins() -> list[dict]:
    init()
    plugins = []
    for path in PLUGINS_DIR.glob("*.py"):
        try:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

            required = ["PLUGIN_NAME", "PLUGIN_SCHEMA", "run"]
            if not all(hasattr(mod, attr) for attr in required):
                console.print(f"  [yellow]⚠ Plugin {path.name} missing required attributes, skipping.[/yellow]")
                continue

            plugins.append({
                "name": mod.PLUGIN_NAME,
                "schema": mod.PLUGIN_SCHEMA,
                "run": mod.run,
            })
            console.print(f"  [dim]✓ Plugin loaded: {mod.PLUGIN_NAME}[/dim]")
        except Exception as e:
            console.print(f"  [red]✗ Failed to load plugin {path.name}: {e}[/red]")
    return plugins


def install_plugin(name: str):
    import httpx
    init()

    try:
        with httpx.Client(timeout=30, verify=True) as client:
            r = client.get(REGISTRY_URL)
            r.raise_for_status()
            registry = r.json()
    except Exception as e:
        console.print(f"[red]✗ Could not fetch plugin registry: {e}[/red]")
        return

    if name not in registry:
        console.print(f"[red]✗ Plugin '{name}' not found in registry.[/red]")
        console.print(f"  Available: {', '.join(registry.keys())}")
        return

    url = registry[name]["url"]
    try:
        with httpx.Client(timeout=30, verify=True) as client:
            r = client.get(url)
            r.raise_for_status()
            plugin_code = r.text
    except Exception as e:
        console.print(f"[red]✗ Could not download plugin: {e}[/red]")
        return

    dest = PLUGINS_DIR / f"{name}.py"
    dest.write_text(plugin_code)
    console.print(f"[green]✓ Plugin '{name}' installed to {dest}[/green]")
    console.print(f"  Restart HelloChusquis to activate it.")


def list_plugins():
    init()
    installed = list(PLUGINS_DIR.glob("*.py"))
    if not installed:
        console.print("[dim]No plugins installed.[/dim]")
        return
    console.print("\n[bold]Installed plugins:[/bold]")
    for p in installed:
        console.print(f"  [cyan]●[/cyan] {p.stem}")
    console.print()


def uninstall_plugin(name: str):
    init()
    path = PLUGINS_DIR / f"{name}.py"
    if not path.exists():
        console.print(f"[red]✗ Plugin '{name}' not found.[/red]")
        return
    path.unlink()
    console.print(f"[green]✓ Plugin '{name}' uninstalled.[/green]")
