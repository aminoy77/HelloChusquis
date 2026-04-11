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

    from main import main as run
    run()


if __name__ == "__main__":
    main()