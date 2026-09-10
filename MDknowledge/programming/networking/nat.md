# NAT essentials

- NAT rewrites private source addresses to public ones at network borders.
- PAT/NAPT multiplexes many hosts onto one public IP via port translation.
- NAT breaks end-to-end connectivity, complicating peer-to-peer protocols.
- STUN/TURN/ICE punch through NATs for WebRTC and VoIP calls.
- Hairpinning lets LAN hosts reach each other via the public address.
- Double NAT (ISP plus home router) compounds port-forwarding pain.
- Carrier-grade NAT shares single IPv4 across whole neighborhoods.
- UPnP/NAT-PMP automate port mapping at malware-abuse risk; prefer manual rules.
- IPv6 eliminates NAT need by restoring abundant public addresses.
- Log translated flows; attribution dies where NAT hides origins.
