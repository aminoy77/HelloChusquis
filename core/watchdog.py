# DEPRECATED: This module is not used. Consider removing.
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from rich.console import Console
console = Console()


class WatchdogHandler(FileSystemEventHandler):
    def __init__(self, callback, pattern="*", ignore_hidden=True):
        self.callback = callback
        self.pattern = pattern
        self.ignore_hidden = ignore_hidden

    def should_process(self, event):
        # Filtrar archivos ocultos si necesario
        if self.ignore_hidden and os.path.basename(event.src_path).startswith('.'):
            return False

        # Comprobar extensión según pattern (simple soporte)
        if "*" not in self.pattern:
            _, ext = os.path.splitext(event.src_path)
            if ext != self.pattern:
                return False
        elif self.pattern.endswith("*"):  # ej. "*.py"
            _, ext = os.path.splitext(event.src_path)
            target_ext = self.pattern[:-1]  # remover '*'
            if not ext.startswith(target_ext):
                return False
        return True

    def on_modified(self, event):
        if not event.is_directory and self.should_process(event):
            console.print(f"[dim]Watchdog: Detected change in {event.src_path}, triggering callback...")
            try:
                self.callback(event.src_path)
            except Exception as e:
                console.print(f"[red]Watcher callback error: {str(e)}[/red]")


def start_watchdog(folder_path: str, trigger_on: str, handler_func, recursive=True):
    observer = Observer()
    event_handler = WatchdogHandler(handler_func, pattern=trigger_on)
    observer.schedule(event_handler, folder_path, recursive=recursive)
    observer.start()
    console.print(f"[green]Watchdog started on '{folder_path}' watching for '{trigger_on}' changes.")
    return observer
