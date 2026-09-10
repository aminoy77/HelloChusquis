# Linux host firewalls

- UFW (`ufw allow 22/tcp`, `ufw enable`) simplifies Ubuntu host firewalls.
- firewalld zones (`public`, `trusted`) scope RHEL rules per interface trust.
- `ufw default deny incoming` plus explicit allows implements least privilege.
- firewalld `--permanent` persists rules surviving reloads and reboots.
- Rate-limit SSH (`limit 22/tcp`) against brute-force password storms.
- Log denials (`ufw logging on`) during incident triage, then quiet down.
- nftables underpins modern stacks; iptables frontend remains for muscle memory.
- Docker inserts its own chains bypassing UFW defaults — audit with `iptables -L`.
- Test from outside hosts; localhost tests skip the very rules under test.
- IPv6 (`ip6tables`/v6 rules) needs parallel policy or it stays wide open.
