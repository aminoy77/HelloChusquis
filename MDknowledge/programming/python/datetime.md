# Python datetime module

- In Python, `datetime.now()` is naive by default; prefer timezone-aware `datetime.now(timezone.utc)`.
- In Python, `date.today()` gives the calendar date and `timedelta(days=7)` spans durations.
- In Python, `strftime('%Y-%m-%d')` formats and `strptime(s, fmt)` parses datetimes.
- In Python, ISO 8601 via `.isoformat()` is the portable interchange format for timestamps.
- In Python, subtracting datetimes yields a `timedelta` with `.days` and `.total_seconds()`.
- In Python, `datetime.fromtimestamp(ts, tz=timezone.utc)` converts epoch seconds safely.
- In Python, naive and aware datetimes cannot be compared; attach timezones first.
- In Python, `zoneinfo.ZoneInfo('Europe/Paris')` handles IANA time zones without extra packages.
- In Python, store and log in UTC, converting to local zones only for display.
- In Python, `time.monotonic()` measures elapsed durations immune to clock adjustments.
