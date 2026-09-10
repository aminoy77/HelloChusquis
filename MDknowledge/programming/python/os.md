# Python os module

- In Python, `os.getcwd()` returns the current directory and `os.chdir(path)` changes it.
- In Python, `os.listdir(path)` lists entries and `os.scandir` yields them lazily with metadata.
- In Python, `os.makedirs(path, exist_ok=True)` creates nested directories without erroring when present.
- In Python, `os.path.join(a, b)` joins paths portably; prefer `pathlib` for new code.
- In Python, `os.environ.get('KEY')` reads environment variables safely with an optional default.
- In Python, `os.cpu_count()` reports logical cores for sizing worker pools.
- In Python, `os.urandom(n)` returns cryptographically strong random bytes for tokens.
- In Python, `os.replace(src, dst)` renames atomically on the same filesystem.
- In Python, `os.walk(root)` traverses directory trees yielding (dirpath, dirnames, filenames).
- In Python, `os.remove` deletes files while `os.rmdir` removes only empty directories.
