# Python pathlib module

- In Python, `Path('a') / 'b'` joins path segments portably with the `/` operator.
- In Python, `p.exists()`, `p.is_file()`, and `p.is_dir()` probe the filesystem safely.
- In Python, `p.read_text(encoding='utf-8')` and `p.write_text(data)` handle whole small files.
- In Python, `p.mkdir(parents=True, exist_ok=True)` creates nested directories idempotently.
- In Python, `p.glob('*.md')` matches one level and `p.rglob('*.py')` recurses fully.
- In Python, `p.suffix`, `p.stem`, `p.name`, and `p.parent` dissect filenames without string hacks.
- In Python, `p.resolve()` absolutizes and `p.expanduser()` expands the leading `~`.
- In Python, `p.stat().st_size` and `p.stat().st_mtime` report size and modification time.
- In Python, `p.rename(target)` moves within filesystems and `p.unlink()` deletes files.
- In Python, `Path.cwd()` and `Path.home()` anchor relative paths to known locations.
