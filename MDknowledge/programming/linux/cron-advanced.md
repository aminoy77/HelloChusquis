# cron and timers

- `flock -n lock cmd` prevents overlapping cron runs of slow jobs.
- MAILTO routes job output to operators instead of local spool silence.
- Randomized sleeps (`sleep $((RANDOM % 300))`) de-thunder fleets of cron hosts.
- systemd `OnCalendar=*-*-* 02:00:00` plus `Persistent=true` beats cron for laptops.
- `AccuracySec=` trades timer precision for wakeup-batched battery life.
- Log start/finish markers to distinguish hangs from never-rans in reviews.
- Exit codes drive alerting; `set -o pipefail` surfaces mid-pipeline failures.
- Keep jobs idempotent: reruns after crashes must converge, not duplicate.
- Version scheduled scripts in git; crontabs referencing /tmp rot silently.
- Monitor last-success timestamps, not just failure alerts, for silent deaths.
