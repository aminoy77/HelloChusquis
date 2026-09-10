# systemd units

- Units declare services, timers, sockets, mounts, and targets declaratively.
- `[Unit]` sets descriptions plus `After=`/`Requires=` ordering and dependencies.
- `[Service]` configures `ExecStart`, restart policies, users, and sandboxing.
- `Restart=on-failure` plus `RestartSec=` revives crashed daemons automatically.
- `[Install]` WantedBy targets wire boot-time enablement correctly.
- Drop-ins (`service.d/override.conf`) customize vendor units upgrade-safely.
- `systemd-analyze blame` ranks boot-time costs for slow-start hunts.
- `PrivateTmp=yes` and `ProtectSystem=strict` sandbox services cheaply.
- Socket activation starts daemons on first connection, saving idle RAM.
- `systemctl cat` plus `systemd-analyze verify` validate edits before reloads.
