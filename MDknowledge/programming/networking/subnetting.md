# Subnetting

- CIDR suffixes set network bits: /24 holds 254 hosts, /16 holds 65k.
- Subnet masks split addresses into network plus host portions bitwise.
- Network address (all-zero host) and broadcast (all-ones) are unusable for hosts.
- Carve subnets by need plus growth headroom, not exact fit.
- VLSM mixes mask lengths per subnet to avoid wasting scarce IPv4.
- Supernetting aggregates routes (`/22` covering four `/24`s) to shrink tables.
- Private ranges (10/8, 172.16/12, 192.168/16) never route on the public internet.
- Plan DNS, DHCP pools, and gateways per subnet before assigning hosts.
- Overlapping subnets across VPCs block peering — coordinate ranges early.
- Document every allocation; mystery ranges cause outage-inducing collisions.
