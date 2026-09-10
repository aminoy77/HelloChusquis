# systemctl basics

- `systemctl status svc` shows state, recent logs, and cgroup placement at once.
- `systemctl start/stop/restart/reload svc` controls units with reload preferred for configs.
- `systemctl enable/disable svc` wires boot-time autostart persistently.
- `systemctl is-active/is-enabled` scripts health and boot checks cleanly.
- `systemctl daemon-reload` applies edited unit files before restarting.
- `systemctl list-units --failed` surfaces the current breakage inventory.
- `systemctl cat svc` prints merged unit definitions with drop-in overrides.
- `systemctl edit --full svc` safely customizes vendor units without editing them.
- `systemd-run --on-calendar` schedules one-shot timers supplanting cron jobs.
- `journalctl -u svc -f` tails a service's logs with `-b` scoping current boot.
