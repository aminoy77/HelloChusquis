import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(__file__))


def parse_args():
    parser = argparse.ArgumentParser(description='Advanced HelloChusquis Terminal Agent')
    parser.add_argument('--profile', choices=['default', 'safe', 'aggressive'], default='default',
                        help='Choose configuration behavior mode')
    parser.add_argument('--unsafe-mode', action='store_true',
                        help='Disable advanced safety checks (expert use only)')
    parser.add_argument('--port', type=int, default=8080,
                        help='Port for API server')
    parser.add_argument('--host', default='0.0.0.0',
                        help='Host for API server')
    parser.add_argument('command', nargs='*', default=[], help='Subcommand and its arguments')

    return parser.parse_args()


def main():
    parsed_args = parse_args()
    args = parsed_args.command

    # Apply profile settings globally
    os.environ["HELLOCHUSQUIS_PROFILE"] = parsed_args.profile
    if parsed_args.unsafe_mode:
        os.environ["HELLOCHUSQUIS_UNSAFE_MODE"] = "1"

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
        from rich.console import Console
        from rich.prompt import Prompt
        ensure_config()
        pool = ProviderPool()
        console = Console()
        console.print("\n[bold cyan]🔧 HelloChusquis Plugin Builder[/bold cyan]\n")
        topic = Prompt.ask("[cyan]What do you want to build?[/cyan]", default="a simple weather plugin")
        plugin_name = Prompt.ask("[cyan]Plugin name[/cyan]", default=topic.lower().replace(" ", "_").replace("-", "_")[:20])
        from core.builder import build_plugin
        result = build_plugin(topic, plugin_name, pool)
        console.print(result)
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

    if args and args[0] == "web":
        import webbrowser
        from rich.console import Console
        console = Console()
        console.print("[cyan]Starting HelloChusquis web interface...[/cyan]")
        console.print("[dim]Open: http://localhost:8000[/dim]")
        webbrowser.open("http://localhost:8000")
        from web.server import start
        start()
        return

    if args and args[0] == "api":
        from core.setup import ensure_config
        from rich.console import Console
        console = Console()
        ensure_config()
        from api.main import start
        parsed = parse_args()
        start(host=parsed.host, port=parsed.port)
        return

    if args and args[0] == "cache":
        from core.cache import clear_cache, get_cache_size
        from rich.console import Console
        console = Console()
        size = get_cache_size()
        cleared = clear_cache()
        console.print(f"[green]Cache cleared! ({cleared} items, {size} bytes freed)[/green]")
        return

    if args and args[0] == "tool":
        from core.tool_builder import build_tool
        from core.setup import ensure_config
        ensure_config()
        tool_name = args[1] if len(args) > 1 else None
        build_tool(tool_name)
        return

    from main import main as run
    run()


if __name__ == "__main__":
    main()