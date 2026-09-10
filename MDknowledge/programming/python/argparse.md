# Python argparse module

- In Python, `ArgumentParser(description=...)` builds CLIs with free `--help` output.
- In Python, `add_argument('--port', type=int, default=8000)` parses typed options with defaults.
- In Python, `action='store_true'` makes boolean flags that default to False.
- In Python, `required=True` enforces mandatory options and `choices=[...]` restricts values.
- In Python, `nargs='?'` takes zero-or-one values and `nargs='*'` gathers zero-or-more.
- In Python, subparsers (`add_subparsers`) route `git`-style multi-command CLIs.
- In Python, `parser.error(msg)` exits with status 2 and usage text on invalid input.
- In Python, `parse_args()` reads `sys.argv`; pass an explicit list in tests.
- In Python, `metavar` and `help=` strings shape readable `--help` screens.
- In Python, `argparse.FileType` opens file arguments directly, closing is still yours.
