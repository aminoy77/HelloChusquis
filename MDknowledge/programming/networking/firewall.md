# Firewalls

- Firewalls filter by IP, port, protocol, and increasingly application identity.
- Default-deny inbound with explicit allows beats default-allow lists.
- Stateful firewalls track connections, permitting return traffic automatically.
- Security groups (cloud) are stateful; NACLs are stateless per-packet lists.
- Egress filtering catches exfiltration and malware callbacks others miss.
- Rule order decides: first match wins in iptables/nftables chains.
- Log drops during incidents; silent discards blind forensic timelines.
- WAFs add HTTP-aware signatures atop network packet filtering.
- Test rules from untrusted networks, not just the allow-listed office.
- Review rules quarterly; stale allows accumulate into Swiss cheese.
