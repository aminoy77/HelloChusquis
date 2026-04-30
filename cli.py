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
    args = parser.parse_args()
    
    if args.command == "web":
        # Start web interface
        from web.server import app
        import uvicorn
        print("Starting HelloChusquis web interface on http://localhost:8000")
        uvicorn.run(app, host="127.0.0.1", port=8000)
    elif args.command == "api":
        # Start API server
        from api.main import app
        import uvicorn
        port = 8080
        if args.args and args.args[0].isdigit():
            port = int(args.args[0])
        print(f"Starting HelloChusquis API on http://localhost:{port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    elif args.command:
        # Pass to main.py for terminal interaction
        # Set the command as input so main.py can handle it
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