# Docker networking

- Compose creates isolated bridge networks per project by default.
- Services resolve each other by name via embedded DNS on custom networks.
- `ports` publish to hosts; `expose` only documents inter-container ports.
- Host networking (`--network host`) drops isolation for speed on Linux.
- Overlay networks span multi-host Swarm clusters transparently.
- Never publish databases publicly; keep them on internal networks only.
- `docker network ls/inspect` audits attachments during connectivity debugging.
- Custom subnets avoid collisions with corporate VPN ranges.
- macvlan grants containers LAN IPs when legacy appliances demand them.
- TLS between services replaces implicit trust on shared networks.
