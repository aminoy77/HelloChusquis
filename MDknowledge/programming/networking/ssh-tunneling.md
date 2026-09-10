# SSH tunneling

- Local forwarding (`-L 8080:db:5432`) reaches private services through bastions.
- Remote forwarding (`-R`) exposes local dev servers to distant collaborators.
- Dynamic forwarding (`-D`) builds a SOCKS proxy for whole-application tunneling.
- Jump hosts (`-J`) chain hops declaratively instead of nested sessions.
- Multiplexing (`ControlMaster`) reuses one connection for instant subsequent shells.
- Keepalives (`ServerAliveInterval`) stop idle firewalls severing sessions.
- Agent forwarding (`-A`) risks key theft on hostile hosts; prefer ProxyJump.
- Reverse tunnels need `GatewayPorts` to bind beyond localhost.
- Tunnel database ports, never expose them publicly, during maintenance.
- Autossh respawns dropped tunnels for persistent links.
