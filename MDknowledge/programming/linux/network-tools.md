# Linux network tools

- `ip addr` shows interfaces and addresses, superseding legacy `ifconfig`.
- `ip route` displays gateways; `ip route add` steers subnets deliberately.
- `ss -tlnp` lists listening TCP sockets with owning processes.
- `ping -c4 host` tests reachability; `mtr` blends ping with traceroute paths.
- `dig +short example.com` resolves DNS records during outages.
- `curl -v` exposes TLS handshakes and redirects behind failures.
- `nc -vz host port` probes TCP reachability in one line.
- `ethtool iface` reports link speed/duplex for duplex-mismatch hunts.
- `tcpdump -i any port 80` captures packets when logs disagree with reality.
- `nmcli` manages NetworkManager profiles on servers and laptops alike.
