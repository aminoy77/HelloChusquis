#!/usr/bin/env python3
"""HelloChusquis CLI wrapper."""
import sys
import os
import argparse
import socket

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

KNOWN_COMMANDS = {"web", "api", "config", "setup", "doctor", "version", "help"}


def pick_free_port(host="127.0.0.1"):
    """Ask the OS for a free ephemeral port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, 0))
        return s.getsockname()[1]
    finally:
        s.close()


def _print_help():
    """Print CLI usage summary."""
    print("""HelloChusquis — autonomous terminal AI agent

Usage:
  hellochusquis                  Start chat REPL (default)
  hellochusquis web              Launch web UI
  hellochusquis api              Launch REST API
  hellochusquis config           Edit configuration
  hellochusquis setup            Run setup wizard
  hellochusquis doctor           Check providers & dependencies
  hellochusquis version          Show version
  hellochusquis help             Show this help

Flags:
  --quick            Quick setup (OpenRouter default)
  --full             Full setup wizard (all providers)
  --show             Show current config (masked keys)
  --api-keys         Edit API keys only
  --providers        Edit providers only
  --port PORT        Port for web/api (default: 8080 api / 7272 web)
  --host HOST        Host for web/api (default: 0.0.0.0 api / 127.0.0.1 web)
  --contracts        Verify bundled integration contracts offline (with doctor)

Examples:
  hellochusquis setup --quick       Quick first-time setup
  hellochusquis web --port 3000     Web UI on port 3000
  hellochusquis config --show       View masked config
  hellochusquis api --host 0.0.0.0  API on all interfaces
""")


def main():
    parser = argparse.ArgumentParser(prog="hellochusquis", add_help=False)
    parser.add_argument("command", nargs="?", default=None, help="Command to run")
    parser.add_argument("args", nargs="*", help="Additional arguments")
    parser.add_argument("--show", action="store_true", help="Show current config")
    parser.add_argument("--api-keys", action="store_true", help="Edit API keys only")
    parser.add_argument("--providers", action="store_true", help="Edit providers only")
    parser.add_argument("--quick", action="store_true", help="Quick setup with OpenRouter only")
    parser.add_argument("--full", action="store_true", help="Full setup wizard with all providers")
    parser.add_argument("--port", type=int, default=None, help="Port for api/web commands (default: 8080 api / 7272 web)")
    parser.add_argument("--host", type=str, default=None, help="Host for api/web commands (default: 0.0.0.0 api / 127.0.0.1 web)")
    parser.add_argument("--contracts", action="store_true", help="Verify integration contracts offline (with doctor)")
    parser.add_argument("--help", action="store_true", dest="show_help", help="Show help message")
    args = parser.parse_args()

    # Handle --help
    if args.show_help:
        _print_help()
        return

    # Handle --quick flag directly (no command needed)
    if args.quick:
        from core.setup import run_quick_setup
        run_quick_setup()
        return

    # Handle --full flag directly
    if args.full:
        from core.setup import run_setup
        run_setup()
        return

    # Handle --show flag directly
    if args.show:
        from core.setup import show_config
        show_config()
        return

    # Handle --api-keys flag directly
    if args.api_keys:
        from core.setup import edit_config
        edit_config("api-keys")
        return

    # Handle --providers flag directly
    if args.providers:
        from core.setup import edit_config
        edit_config("providers")
        return

    # --- Command dispatch ---

    if args.command == "help":
        _print_help()
        return

    if args.command == "version":
        try:
            from core.version import __version__
            print(f"hellochusquis {__version__}")
        except ImportError:
            print("hellochusquis (version unknown)")
        return

    if args.command == "setup":
        from core.setup import run_quick_setup, run_setup
        if args.full:
            run_setup()
        else:
            run_quick_setup()
        return

    if args.command == "config":
        from core.setup import show_config, edit_config, ensure_config

        if args.show:
            show_config()
            return

        section = None
        if args.api_keys:
            section = "api-keys"
        elif args.providers:
            section = "providers"

        edit_config(section)
        return

    if args.command == "web":
        from web.server import start
        host = args.host or "127.0.0.1"
        port = args.port or 7272

        if port == 7272:
            # Default port: use 7272 if free, else pick a random free port.
            probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                probe.bind((host, 7272))
                probe.close()
            except OSError:
                port = pick_free_port(host)
                print(f"Port 7272 unavailable; using random port {port}")

        print(f"Starting HelloChusquis web interface on http://{host}:{port}")
        start(host=host, port=port)
        return

    if args.command == "api":
        from api.main import app
        import uvicorn
        host = args.host or "0.0.0.0"
        port = args.port or 8080
        print(f"Starting HelloChusquis API on http://{host}:{port}")
        uvicorn.run(app, host=host, port=port)
        return

    if args.command == "doctor":
        if args.contracts:
            from core.integration_contracts import check_integration_contracts, contract_summary
            results = check_integration_contracts()
            summary = contract_summary(results)
            print(
                f"Integration contracts: {summary['passed']}/{summary['total']} passed "
                f"({summary['failed']} failed)"
            )
            for result in results:
                marker = "PASS" if result.ok else "FAIL"
                print(f"  [{marker}] {result.name}: {result.detail}")
            return 0 if summary["failed"] == 0 else 1
        from core.setup import ensure_config, console
        from rich.panel import Panel
        try:
            config = ensure_config(interactive=False)
        except FileNotFoundError:
            console.print("[red]No providers configured.[/red]")
            console.print("[dim]Run: hellochusquis setup[/dim]")
            return
        providers = config.get("providers", [])

        console.print(Panel(
            "[bold #f5a623]Doctor Check[/bold #f5a623]",
            expand=False
        ))

        if not providers:
            console.print("[red]No providers configured.[/red]")
            console.print("[dim]Run: hellochusquis setup[/dim]")
            return

        for p in providers:
            name = p.get("name", "Unknown")
            api_key = p.get("api_key", "")
            base_url = p.get("base_url", "")
            if not api_key or len(api_key.strip()) == 0:
                console.print(f"  [red]✗[/red] {name} — [red]empty API key[/red]")
            elif "localhost" in base_url and api_key == "ollama":
                console.print(f"  [yellow]?[/yellow] {name} — [yellow]Ollama (check if running)[/yellow]")
            else:
                console.print(f"  [green]✓[/green] {name} — key configured")

        console.print("\n[dim]Edit config: hellochusquis config[/dim]")
        return

    # Validate unknown commands
    if args.command is not None:
        print(f"Unknown command '{args.command}'. Try: web, api, config, setup, or nothing for chat.")
        print("Run 'hellochusquis help' for full usage.")
        sys.exit(1)

    # No command → start chat REPL
    from main import main as chat_main
    sys.exit(chat_main())


if __name__ == "__main__":
    main()
