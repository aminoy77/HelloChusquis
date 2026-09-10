# Python configparser

- In Python, `configparser` reads INI files into sectioned dictionaries.
- In Python, `config.read('app.ini')` silently ignores missing files — verify with its return list.
- In Python, `config['db']['host']` accesses values with interpolation by default.
- In Python, `RawConfigParser` disables `%` interpolation for literal values.
- In Python, `config.write(f)` persists edits preserving most structure.
- In Python, `fallbacks` (`get('s','k', fallback='x')`) supply defaults cleanly.
- In Python, environment-plus-secret managers beat INI for sensitive values.
- In Python, TOML (`tomllib`) supersedes INI for modern Python configuration.
