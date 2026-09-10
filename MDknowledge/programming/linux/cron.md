# cron basics

- Cron fields read minute, hour, day-of-month, month, day-of-week left to right.
- `*/15 * * * *` runs quarterly-hourly; `0 2 * * *` runs nightly at 2am.
- `crontab -e` edits personal tables; `/etc/cron.d/` hosts system jobs with users.
- Absolute paths plus explicit env vars prevent cron's minimal-environment surprises.
- Redirect output (`>> log 2>&1`) or cron mails local output per run.
- Lock with `flock` to stop overlapping runs of slow jobs.
- `@reboot`, `@daily` shorthands cover common schedules readably.
- systemd timers supersede cron with logging, dependencies, and calendars.
- Test commands interactively first; cron failures hide silently by default.
- Log job start/finish lines to distinguish hangs from never-rans.
