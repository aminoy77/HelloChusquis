# Python venv and pip

- `python -m venv .venv` creates isolated project environments reproducibly.
- Activate via `source .venv/bin/activate` (or `.venv\Scripts\activate` on Windows).
- `pip install -r requirements.txt` pins installs; `pip freeze` captures them.
- Never `sudo pip install`: system Python belongs to the OS package manager.
- `pip install -e .` links local packages editable for development loops.
- `pip cache purge` reclaims gigabytes when disk runs short.
- `python -m pip` guarantees the pip matching the running interpreter.
- Virtualenvs are disposable: delete and recreate rather than debugging them.
- `.venv/` belongs in `.gitignore`, never in version control.
- Containers often skip venvs (already isolated) but pin requirements equally.
