# Python logging module

- In Python, `logging.getLogger(__name__)` scopes loggers per module for filterable output.
- In Python, levels rank DEBUG < INFO < WARNING < ERROR < CRITICAL for threshold filtering.
- In Python, `logging.basicConfig(level=...)` configures the root handler once at startup.
- In Python, `%s`-style lazy args (`log.info('x=%s', x)`) skip formatting when the level is off.
- In Python, `logger.exception('msg')` inside `except` blocks attaches the traceback automatically.
- In Python, handlers route records to streams, files, or rotation policies independently.
- In Python, `RotatingFileHandler` caps log disk usage by size with backup counts.
- In Python, `logger.setLevel` per module quiets noisy libraries without muting your app.
- In Python, structured JSON formatters make logs greppable by machines and humans.
- In Python, never `print` in libraries; emit logs and let applications configure output.
