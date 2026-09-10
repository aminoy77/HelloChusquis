# DHCP essentials

- DHCP auto-assigns IPs via Discover, Offer, Request, Acknowledge (DORA).
- Leases expire and renew; short leases suit guest churn, long ones stable servers.
- Reservations pin IPs to MACs for printers and servers needing fixity.
- DHCP options push gateways, DNS, NTP, and boot images alongside addresses.
- Rogue DHCP servers hijack traffic; snooping switches block untrusted offers.
- APIPA (169.254.x.x) signals DHCP failure, not valid configuration.
- Relay agents forward broadcasts across subnets to central servers.
- Scope exhaustion drops new joins first — monitor pool utilization.
- Static critical infrastructure (routers, DNS) outside DHCP pools.
- IPv6 prefers SLAAC/router advertisements over stateful DHCPv6 mostly.
