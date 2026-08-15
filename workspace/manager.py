from pathlib import Path
from rich.prompt import Confirm
from rich.console import Console

console = Console()

# Always-allowed user directories
_ALWAYS_ALLOWED = [
    "Downloads",
    "Documents",
    "Desktop",
    "Pictures",
    "Music",
    "Movies",
    "workspace",
]


class WorkspaceManager:
    def __init__(self, initial_dirs: list[str]):
        self.allowed = [Path(d).expanduser().resolve() for d in initial_dirs]
        # Always allow home directory and common user folders
        home = Path.home()
        for folder in _ALWAYS_ALLOWED:
            p = home / folder
            if p.exists() and p not in self.allowed:
                self.allowed.append(p)

    def is_allowed(self, path: str) -> bool:
        p = Path(path).expanduser().resolve()
        # Always allow anything under home directory
        if str(p).startswith(str(Path.home())):
            return True
        return any(p == d or d in p.parents for d in self.allowed)

    def request_access(self, path: str) -> bool:
        p = Path(path).expanduser().resolve()
        if self.is_allowed(path):
            return True
        console.print(f"\n[yellow]⚠ HelloChusquis wants access to:[/yellow] {p}")
        granted = Confirm.ask("Allow?", default=True)
        if granted:
            self.allowed.append(p)
            console.print(f"[green]✓ Access granted[/green]")
        else:
            console.print(f"[red]✗ Access denied[/red]")
        return granted

    def list_allowed(self) -> list[str]:
        return [str(d) for d in self.allowed]