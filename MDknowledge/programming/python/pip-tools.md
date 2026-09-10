# Python packaging

- `pyproject.toml` declares metadata plus build backend for modern packaging.
- `pip install package` fetches from PyPI resolving dependencies automatically.
- Version specifiers (`>=1.2,<2`) bound compatibility deliberately.
- `pip-tools compile` freezes transitive pins into lock files reproducibly.
- Entry points (`[project.scripts]`) install CLI commands alongside libraries.
-  Wheels (`pip wheel`) prebuild binaries skipping CI compiler toolchains.
- `twine upload` publishes releases; TestPyPI rehearses first safely.
- Semantic versioning (major.minor.patch) signals breaking versus additive change.
- Changelogs per release beat git-log archaeology for upgraders.
- Yank releases (don't delete) to preserve resolvable history.
