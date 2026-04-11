import sys
import os
sys.path.insert(0, os.path.dirname(__file__))


def main():
    args = sys.argv[1:]

    if args and args[0] == "install" and len(args) > 1:
        from core.plugins import install_plugin
        install_plugin(args[1])
        return

    if args and args[0] == "uninstall" and len(args) > 1:
        from core.plugins import uninstall_plugin
        uninstall_plugin(args[1])
        return

    if args and args[0] == "plugins":
        from core.plugins import list_plugins
        list_plugins()
        return

    if args and args[0] == "build":
        from core.setup import ensure_config
        from core.provider import ProviderPool
        ensure_config()
        pool = ProviderPool()
        from core.builder import build_plugin
        build_plugin(pool)
        return

    if args and args[0] == "learn":
        from core.setup import ensure_config
        from core.learning import load_learnings
        from rich.console import Console
        import json
        ensure_config()
        console = Console()
        learnings = load_learnings()
        console.print("\n[bold]Current learnings:[/bold]")
        console.print_json(json.dumps(learnings, indent=2, ensure_ascii=False))
        return

    from main import main as run
    run()


if __name__ == "__main__":
    main()