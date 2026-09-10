# Log rotation

- logrotate prevents runaway logs from filling disks on long-lived hosts.
- `/etc/logrotate.d/` drop-ins configure per-application policies cleanly.
- `daily/weekly/size 100M` plus `rotate 14` bound retention predictably.
- `compress` plus `delaycompress` shrink archives while today's stays readable.
- `copytruncate` rotates without signaling daemons that cannot reopen logs.
- `postrotate` scripts (e.g. `kill -USR1`) notify daemons to reopen handles.
- `missingok` tolerates absent files; `notifempty` skips zero-byte rotations.
- `logrotate -d` debugs configs dry-run style before they bite at 3am.
- Journal `SystemMaxUse=` caps systemd logs where logrotate does not reach.
- Ship to central aggregation before local rotation deletes evidence.
