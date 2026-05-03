#!/usr/bin/env python3
"""HelloChusquis CLI wrapper."""
import sys
import os
import argparse

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    parser = argparse.ArgumentParser(prog="hellochusquis")
    parser.add_argument("command", nargs="?", default=None, help="Command to run")
    parser.add_argument("args", nargs="*", help="Additional arguments")
    parser.add_argument("--show", action="store_true", help="Show current config")
    parser.add_argument("--api-keys", action="store_true", help="Edit API keys only")
    parser.add_argument("--providers", action="store_true", help="Edit providers only")
    parser.add_argument("--quick", action="store_true", help="Quick setup (one question)")
    parser.add_argument("--full", action="store_true", help="Full setup wizard")
    args = parser.parse_args()
    
    if args.command == "setup":
        from core.setup import run_quick_setup, run_setup
        if args.full:
            run_setup()
        else:
            run_quick_setup()
        return
    
    if args.command == "config" or args.show:
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
        from web.server import app
        import uvicorn
        print("Starting HelloChusquis web interface on http://localhost:8000")
        uvicorn.run(app, host="127.0.0.1", port=8000)
        return
    
    if args.command == "api":
        from api.main import app
        import uvicorn
        port = 8080
        if args.args and args.args[0].isdigit():
            port = int(args.args[0])
        print(f"Starting HelloChusquis API on http://localhost:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
        return
    
    if args.command:
        if args.command.startswith("/"):
            sys.argv = ["main.py", args.command]
        else:
            sys.argv = ["main.py"]
        from main import main
        sys.exit(main())
    else:
        from main import main
        sys.exit(main())

if __name__ == "__main__":
    main()