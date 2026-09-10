# DNS essentials

- DNS translates human names to IP addresses hierarchically from the root.
- A records map names to IPv4 and AAAA records to IPv6 addresses.
- CNAME aliases one name to another; the apex domain needs A/ALIAS records instead.
- MX records route incoming mail to handling servers by priority.
- TXT records carry SPF, DKIM, and verification tokens for domains.
- NS records delegate zones to authoritative nameservers.
- TTL seconds control how long resolvers cache each record before refetching.
- Propagation is really cache expiry: lower TTLs before migrations, then raise after.
- DNSSEC signs zones cryptographically against spoofed answers.
- `dig +short` and `nslookup` query records directly during outages.
