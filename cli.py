#!/usr/bin/env python3
"""HelloChusquis CLI wrapper."""
import sys
import os
import argparse
import socket

# No sys.path insert needed: running as a script puts this directory on the
# path automatically, and a console-script install covers the rest. The old
# dirname(dirname(...)) added the PARENT folder (e.g. ~/Desktop), letting
# sibling projects shadow our core/ and config modules.


def _open_browser(host: str, port: int) -> None:
    """Open the web UI in the default browser (best-effort, never fails)."""
    import webbrowser

    shown = "127.0.0.1" if host in ("0.0.0.0", "::") else host
    try:
        webbrowser.open(f"http://{shown}:{port}")
    except Exception:
        pass


def pick_free_port(host="127.0.0.1"):
    """Ask the OS for a free ephemeral port."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind((host, 0))
        return s.getsockname()[1]
    finally:
        s.close()


def _print_contract_summary() -> int:
    """Print offline integration-contract results and return a shell-style status."""
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


def _run_users_command(subcommand: str, arguments: list[str], role: str) -> int:
    """Manage the principals that may authenticate against the HTTP surfaces."""
    from core.identity import IdentityError, default_store, parse_role

    store = default_store()
    if subcommand in ("", "list"):
        principals = store.list_principals()
        if not principals:
            print("No users yet. Create one with: hellochusquis users add <name> --role operator")
            return 0
        for principal in principals:
            state = "active" if principal.is_active else f"revoked {principal.revoked_at}"
            print(f"{principal.name:<24} {principal.role.value:<9} {principal.id}  {state}")
        return 0

    if subcommand == "add":
        if not arguments:
            print("Usage: hellochusquis users add <name> [--role viewer|operator|owner]")
            return 1
        try:
            principal, token = store.create(arguments[0], parse_role(role))
        except IdentityError as exc:
            print(f"Error: {exc}")
            return 1
        print(f"Created {principal.name} ({principal.role.value}).")
        print(f"Token (shown once, store it now): {token}")
        return 0

    if subcommand == "revoke":
        if not arguments:
            print("Usage: hellochusquis users revoke <name>")
            return 1
        try:
            principal = store.revoke(arguments[0])
        except IdentityError as exc:
            print(f"Error: {exc}")
            return 1
        print(f"Revoked {principal.name}.")
        return 0

    print(f"Unknown users subcommand '{subcommand}'. Try: list, add, revoke.")
    return 1


def resolve_login_name(arg: str):
    """Map a CLI --login argument to an OAUTH_PROVIDERS display name."""
    from core.oauth import OAUTH_PROVIDERS
    if not arg:
        return None
    aliases = {"copilot": "GitHub Copilot", "ghc": "GitHub Copilot",
               "github copilot": "GitHub Copilot", "qwen": "Qwen"}
    low = arg.strip().lower()
    if low in aliases:
        return aliases[low]
    for name in OAUTH_PROVIDERS:
        if name.lower() == low:
            return name
    return None


def _print_help():
    """Print CLI usage summary."""
    print("""HelloChusquis — autonomous terminal AI agent

Usage:
  hellochusquis                  Start chat REPL (default)
  hellochusquis web              Launch web UI
  hellochusquis api              Launch REST API
  hellochusquis telegram         Chat from Telegram (needs bot token)
  hellochusquis config           Edit configuration
  hellochusquis setup            Run setup wizard
  hellochusquis status           Show local readiness summary
  hellochusquis doctor           Check providers & dependencies
  hellochusquis models           List configured providers and models
  hellochusquis memory [QUERY]   Memory stats, search, or remember|forget FACT
  hellochusquis knowledge        Knowledge base stats (--reingest to refresh)
  hellochusquis skills list      List installed SKILL.md skills
  hellochusquis skills show NAME Show a skill body
  hellochusquis users list       List HTTP users and their roles
  hellochusquis users add NAME   Create a user and print its token once
  hellochusquis users revoke NAME  Revoke a user's token
  hellochusquis version          Show version
  hellochusquis help             Show this help

Flags:
  --quick            Quick setup (OpenRouter default)
  --full             Full setup wizard (all providers)
  --show             Show current config (masked keys)
  --api-keys         Edit API keys only
  --providers        Edit providers only
  --port PORT        Port for web/api (default: 8080 api / 7272 web)
  --host HOST        Host for web/api (default: 127.0.0.1)
  --contracts        Verify bundled integration contracts offline (with doctor)
  --live             Ping each provider endpoint (with doctor)
  --no-browser       Don't auto-open the browser (with web)
  --role ROLE        Role for 'users add': viewer, operator or owner (default: operator)
  --token TOKEN      Telegram bot token (or HELLOCHUSQUIS_TELEGRAM_TOKEN)
  --allow IDS        Telegram chat IDs, comma-separated (or HELLOCHUSQUIS_TELEGRAM_ALLOW)

Examples:
  hellochusquis setup --quick       Quick first-time setup
  hellochusquis web --port 3000     Web UI on port 3000
  hellochusquis telegram --allow 123456789
                            Telegram bridge for your chat
  hellochusquis config --show       View masked config
  hellochusquis status              Check local readiness
  hellochusquis api --host 0.0.0.0  API on all interfaces
""")


def main():
    parser = argparse.ArgumentParser(prog="hellochusquis", add_help=False)
    parser.add_argument("command", nargs="?", default=None, help="Command to run")
    parser.add_argument("args", nargs="*", help="Additional arguments")
    parser.add_argument("--show", action="store_true", help="Show current config")
    parser.add_argument("--api-keys", action="store_true", help="Edit API keys only")
    parser.add_argument("--providers", action="store_true", help="Edit providers only")
    parser.add_argument("--login", type=str, default=None, metavar="PROVIDER", help="Login to an OAuth provider via browser (copilot, qwen)")
    parser.add_argument("--quick", action="store_true", help="Quick setup with OpenRouter only")
    parser.add_argument("--full", action="store_true", help="Full setup wizard with all providers")
    parser.add_argument("--port", type=int, default=None, help="Port for api/web commands (default: 8080 api / 7272 web)")
    parser.add_argument("--host", type=str, default=None, help="Host for api/web commands (default: 127.0.0.1)")
    parser.add_argument("--contracts", action="store_true", help="Verify integration contracts offline (with doctor)")
    parser.add_argument("--live", action="store_true", help="Ping each provider endpoint (with doctor)")
    parser.add_argument("--no-browser", action="store_true", help="Don't auto-open the browser (with web)")
    parser.add_argument("--reingest", action="store_true", help="Force knowledge reingest (with knowledge)")
    parser.add_argument("--role", type=str, default="operator", help="Role for 'users add' (viewer, operator, owner)")
    parser.add_argument("--token", type=str, default=None, help="Telegram bot token")
    parser.add_argument("--allow", type=str, default=None, help="Telegram chat IDs, comma-separated")
    parser.add_argument("--help", action="store_true", dest="show_help", help="Show help message")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    args = parser.parse_args()

    # Handle --help
    if args.show_help:
        _print_help()
        return

    # Handle --version
    if args.version:
        try:
            from core.version import __version__
            print(f"hellochusquis {__version__}")
        except ImportError:
            print("hellochusquis (version unknown)")
        return

    # Handle --quick flag directly (no command needed)
    if args.quick and args.command is None:
        from core.setup import run_quick_setup
        run_quick_setup()
        return

    # Handle --full flag directly
    if args.full and args.command is None:
        from core.setup import run_setup
        run_setup()
        return

    # Handle --show flag directly
    if args.show and args.command is None:
        from core.setup import show_config
        show_config()
        return

    # Handle --api-keys flag directly
    if args.api_keys and args.command is None:
        from core.setup import edit_config
        edit_config("api-keys")
        return

    # Handle --providers flag directly
    if args.providers and args.command is None:
        from core.setup import edit_config
        edit_config("providers")
        return

    # Handle --login flag directly
    if args.login and args.command is None:
        name = resolve_login_name(args.login)
        if not name:
            from core.oauth import OAUTH_PROVIDERS
            print(f"Unknown OAuth provider '{args.login}'. Valid: {', '.join(OAUTH_PROVIDERS)}")
            return 1
        from core.setup import ensure_config, login_provider
        config = ensure_config()
        entry = login_provider(config, name)
        return 0 if entry else 1

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

    if args.command == "status":
        from core.setup import ensure_config

        try:
            config = ensure_config(interactive=False)
        except FileNotFoundError:
            print("Status: setup required. Run: hellochusquis setup")
        else:
            providers = config.get("providers", [])
            configured = sum(
                1
                for provider in providers
                if provider.get("api_key", "").strip()
                or "localhost" in provider.get("base_url", "").lower()
            )
            print(
                f"Status: {configured}/{len(providers)} provider(s) configured. "
                "Run 'hellochusquis doctor' for provider details."
            )
            from core.setup import find_config_shadows
            active, _ = find_config_shadows()
            if active:
                print(f"Config: {active}")
            try:
                import core.db_memory as db_memory
                store = db_memory._get_store()
                print(
                    f"Memory: {store.get_session_count()} sessions, "
                    f"{store.get_entry_count()} entries, "
                    f"{db_memory.kb_ingested_count()} KB sources."
                )
            except Exception:
                pass

        if args.contracts:
            _print_contract_summary()
        return

    if args.command == "users":
        subcommand = args.args[0] if args.args else "list"
        sys.exit(_run_users_command(subcommand, args.args[1:], args.role))

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
        if host in ("0.0.0.0", "::"):
            print("Open http://127.0.0.1:%d in your browser." % port)
        if not args.no_browser:
            _open_browser(host, port)
        start(host=host, port=port)
        return

    if args.command == "telegram":
        from core.telegram_bridge import TelegramAPI, TelegramBridge
        token = args.token or os.environ.get("HELLOCHUSQUIS_TELEGRAM_TOKEN", "")
        allow = args.allow or os.environ.get("HELLOCHUSQUIS_TELEGRAM_ALLOW", "")
        if not token:
            print("Missing bot token. Talk to @BotFather, then:")
            print("  hellochusquis telegram --token <token> --allow <your-chat-id>")
            print("  (or set HELLOCHUSQUIS_TELEGRAM_TOKEN / HELLOCHUSQUIS_TELEGRAM_ALLOW)")
            return 1
        try:
            allow_ids = {int(x) for x in str(allow).split(",") if x.strip()}
        except ValueError:
            print("Invalid --allow value. Use comma-separated Telegram chat IDs.")
            return 1
        if not allow_ids:
            print("Refusing to start an open bot. Pass --allow <your-chat-id> first.")
            print("Tip: message @userinfobot to learn your chat ID.")
            return 1
        from core.setup import ensure_config
        from core.agent import Agent
        config = ensure_config()
        agents = {}

        def handle(chat_id, text):
            agent = agents.get(chat_id)
            if agent is None:
                agent = Agent(config, session_key=f"telegram:{chat_id}")
                agents[chat_id] = agent
            if not agent.try_acquire_turn():
                return "Busy with your previous message, try again in a moment."
            try:
                if text == "/clear":
                    agent.clear_conversation()
                    return "History cleared."
                return agent.run(text)
            except RuntimeError:
                return "The request could not be completed. Check server logs."
            finally:
                agent.release_turn()

        bridge = TelegramBridge(TelegramAPI(token).call, handle, allow_ids)
        print(f"Telegram bridge listening for {len(allow_ids)} chat(s). Ctrl+C to stop.")
        try:
            bridge.run_forever()
        except KeyboardInterrupt:
            print("\nStopped.")
        return

    if args.command == "api":
        from api.main import app
        import uvicorn
        host = args.host or "127.0.0.1"
        port = args.port or 8080
        if port == 8080:
            probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                probe.bind((host, 8080))
                probe.close()
            except OSError:
                port = pick_free_port(host)
                print(f"Port 8080 unavailable; using random port {port}")
        print(f"Starting HelloChusquis API on http://{host}:{port}")
        if host in ("0.0.0.0", "::"):
            print("Send requests to http://127.0.0.1:%d from this machine." % port)
        uvicorn.run(app, host=host, port=port)
        return

    if args.command == "doctor":
        if args.contracts:
            return _print_contract_summary()
        from core.setup import ensure_config, console, find_config_shadows, live_check_provider
        from core.setup import find_duplicate_providers, check_workspace_dirs, count_kb_files
        from core.setup import check_ports_free, check_browser_ready, _is_local_url
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

        _, shadowed = find_config_shadows()
        for extra in shadowed:
            console.print(f"[yellow]![/yellow] [yellow]Shadowed config ignored: {extra} (delete if stale)[/yellow]")

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
            elif _is_local_url(base_url):
                ok, _, ms = live_check_provider(p, timeout=1.0)
                if ok:
                    console.print(f"  [green]✓[/green] {name} — [green]local, responding ({ms:.0f}ms)[/green]")
                else:
                    console.print(f"  [red]✗[/red] {name} — [red]local server not running at {base_url}[/red]")
            else:
                console.print(f"  [green]✓[/green] {name} — key configured")
            if args.live:
                ok, detail, ms = live_check_provider(p)
                if ok:
                    console.print(f"    [green]✓[/green] [dim]live {ms:.0f}ms ({detail})[/dim]")
                else:
                    console.print(f"    [red]✗[/red] [red]unreachable: {detail}[/red]")

        console.print("\n[dim]Edit config: hellochusquis config[/dim]")

        for dup in find_duplicate_providers(providers):
            console.print(f"[yellow]![/yellow] [yellow]Duplicate provider: {dup} (remove one in config)[/yellow]")
        _active_cfg, _ = find_config_shadows()
        if _active_cfg:
            console.print(f"[dim]Active config: {_active_cfg}[/dim]")
        for path, exists in check_workspace_dirs(config.get("settings", {}).get("workspace_dirs", [])):
            if not exists:
                console.print(f"[yellow]![/yellow] [yellow]Workspace missing: {path}[/yellow]")
        console.print(f"[dim]Knowledge base: {count_kb_files()} files[/dim]")
        from core import db_memory as _dbm
        if count_kb_files() > 0 and _dbm.kb_ingested_count() == 0:
            console.print("[yellow]![/yellow] [yellow]Knowledge not ingested yet (starts on next chat/web session)[/yellow]")
        elif _dbm.kb_ingested_count() < count_kb_files():
            console.print("[dim]Knowledge: reingest pending (new files since last load)[/dim]")
        for port, free in check_ports_free([7272, 8080]).items():
            if not free:
                console.print(f"[yellow]![/yellow] [yellow]Port {port} in use[/yellow]")
        ok, hint = check_browser_ready()
        console.print(f"[dim]Browser automation: {'ready' if ok else hint}[/dim]")
        return

    if args.command == "models":
        from core.setup import ensure_config
        try:
            config = ensure_config(interactive=False)
        except FileNotFoundError:
            print("No providers configured. Run: hellochusquis setup")
            return
        needle = " ".join(args.args).strip().lower()
        for p in config.get("providers", []):
            if needle and needle not in p.get("name", "").lower():
                continue
            key_tag = "" if (p.get("api_key") or "").strip() else " (no key)"
            print(f"{p.get('name', 'Unknown')}{key_tag} — {p.get('model', 'no model')} [{p.get('base_url', '')}]")
        return

    if args.command == "memory":
        import core.db_memory as db_memory
        rest = args.args
        if rest and rest[0] == "remember" and len(rest) > 1:
            fact = " ".join(rest[1:])
            db_memory._get_store().add_entry(key="note", value=fact, category="fact", importance=6)
            print(f"Remembered: {fact}")
        elif rest and rest[0] == "forget" and len(rest) > 1:
            n = db_memory.forget_matching(" ".join(rest[1:]))
            print(f"Forgot {n} memories.")
        elif rest and rest[0] == "sessions":
            for s in db_memory._get_store().load_sessions(limit=10):
                msgs = s.get("data", [])
                print(f"{s.get('timestamp', '?')}  {len(msgs)} messages")
        elif rest and rest[0] == "prune" and len(rest) > 1:
            try:
                days = int(rest[1])
            except ValueError:
                print("Usage: hellochusquis memory prune <days>")
                return
            print(f"Pruned {db_memory.prune_sessions_older_than(days)} old sessions.")
        elif rest and rest[0] == "export" and len(rest) > 1:
            import tempfile
            from pathlib import Path as _Path
            dest = _Path(rest[1]).expanduser()
            store = db_memory._get_store()
            lines = ["# HelloChusquis memory export", ""]
            # Page until exhausted: a hard limit silently drops history.
            page = 500
            offset = 0
            while True:
                batch = store.load_sessions(limit=page, offset=offset)
                if not batch:
                    break
                for s in batch:
                    lines.append(f"## {s.get('timestamp', '?')}")
                    for m in s.get("data", []):
                        lines.append(f"- **{m.get('role', '?')}:** {m.get('content', '')}")
                    lines.append("")
                offset += page
            for e in store.list_entries(limit=100000):
                lines.append(f"- [{e.category or 'fact'}] {e.key}: {e.value}")
            # Atomic write: never truncate the old export before the new one is complete.
            fd, tmp_name = tempfile.mkstemp(dir=dest.parent, suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
            os.replace(tmp_name, dest)
            print(f"Exported to {dest}")
        elif rest:
            query = " ".join(rest)
            entries = db_memory._get_store().search_entries_keyword(query, limit=5)
            if not entries:
                print("No matching memories.")
            for e in entries:
                when = (e.created_at or "")[:10]
                print(f"[{when} {e.category or 'memory'}] {e.key}: {e.value[:160]}".replace("\n", " "))
        else:
            store = db_memory._get_store()
            print(f"sessions: {store.get_session_count()}  entries: {store.get_entry_count()}")
            summary = db_memory.load_summary()
            print(f"summary: {(summary[:120] + '...') if len(summary) > 120 else summary or '(none)'}")
            try:
                from core.learning import load_learnings
                learnings = load_learnings()
                print(f"learnings: {len(learnings.get('tool_patterns', {}))} patterns, "
                      f"{len(learnings.get('system_prompt_improvements', []))} improvements")
            except Exception:
                pass
        return

    if args.command == "knowledge":
        import core.db_memory as db_memory
        from core.setup import count_kb_files
        if args.reingest:
            store = db_memory._get_store()
            store.conn.execute("DELETE FROM kb_sources")
            store.conn.commit()
            n = db_memory.load_knowledge()
            print(f"Reingested {n} facts.")
        else:
            print(f"files: {count_kb_files()}  ingested sources: {db_memory.kb_ingested_count()}")
        return

    if args.command == "skills":
        from pathlib import Path as _Path
        from core import skills as _skills
        sub = args.args[0] if args.args else "list"
        reg = _skills.SkillRegistry(skills_dir=str(_Path.home() / ".hellochusquis" / "skills-json"))
        reg.discover_skill_md([
            str(_Path.home() / ".hellochusquis" / "skills"),
            str(_Path(__file__).resolve().parent / ".agents" / "skills"),
        ])
        if sub == "list":
            items = reg.list_skills()
            if not items:
                print("No skills installed. Drop SKILL.md folders in ~/.hellochusquis/skills/<name>/SKILL.md.")
            else:
                for item in items:
                    print(f"{item['name']}: {item.get('description', '')}")
        elif sub == "show":
            name = args.args[1] if len(args.args) > 1 else ""
            skill = reg.skills.get(name)
            if skill is None or not skill.prompt_template:
                print(f"Skill not found: {name}")
                return 1
            print(skill.prompt_template[:8000])
        else:
            print(f"Unknown skills subcommand '{sub}'. Try: list, show <name>.")
            return 1
        return

    # Validate unknown commands
    if args.command is not None and args.command not in {
        "web", "api", "telegram", "config", "setup", "status", "users",
        "doctor", "version", "help", "models", "memory", "knowledge", "skills",
    }:
        print(f"Unknown command '{args.command}'. Try: web, api, telegram, config, setup, status, or nothing for chat.")
        print("Run 'hellochusquis help' for full usage.")
        sys.exit(1)

    # No command → start chat REPL
    from main import main as chat_main
    sys.exit(chat_main())


if __name__ == "__main__":
    sys.exit(main())
