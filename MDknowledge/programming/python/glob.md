# Python glob module

- In Python, `glob.glob('*.md')` lists matches in the current directory non-recursively.
- In Python, `glob.glob('**/*.py', recursive=True)` descends the whole tree.
- In Python, `glob.iglob` yields lazily for huge directory trees.
- In Python, `*` skips dotfiles and (without recursive) directory separators.
- In Python, `?` matches one character and `[abc]` matches one of the set.
- In Python, `glob.escape(path)` quotes metacharacters in user-supplied segments.
- In Python, results order is arbitrary; wrap with `sorted()` for determinism.
- In Python, prefer `pathlib.Path.glob`/`rglob` for object-oriented results in new code.
- In Python, `glob` follows the OS case rules, so patterns may match case-insensitively on macOS/Windows.
- In Python, combine `glob` with `os.path.isfile` filters when directories can match.
