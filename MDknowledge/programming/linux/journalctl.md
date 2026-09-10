# journalctl basics

- `journalctl -f` tails all logs live; `-u svc` scopes to one service.
- `journalctl -b` limits to the current boot, `-b -1` to the previous one.
- `journalctl --since '1 hour ago'` windows investigations precisely.
- `journalctl -p err` filters priority err and above for triage.
- `journalctl -o json-pretty` structures entries for scripted analysis.
- `journalctl --disk-usage` plus `--vacuum-size=500M` caps log storage.
- `journalctl _PID=1234` isolates one process's entries across units.
- `journalctl -k` shows kernel messages for hardware/driver faults.
- Persistent journals need `/var/log/journal/`; else logs vanish on reboot.
- Forward to central aggregation before local rotation deletes evidence.
