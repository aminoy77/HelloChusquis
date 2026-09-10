# IPv4 and IPv6

- IPv4's 32-bit space (~4.3B addresses) exhausted; NAT stretches it at complexity cost.
- IPv6's 128-bit space restores end-to-end addressing without NAT hacks.
- IPv6 abbreviates with `::` once per address for the longest zero run.
- Dual-stack hosts speak both families, preferring IPv6 where available.
- Link-local (`fe80::/10`) addresses never route beyond their segment.
- ULA (`fd00::/8`) provides private IPv6 space like RFC1918 IPv4 ranges.
- AAAA records publish IPv6 endpoints alongside classic A records.
- NAT66 is discouraged; IPv6 restores the end-to-end principle instead.
- Migration blockers are usually legacy middleboxes, not protocols.
- Log both families; attackers hide in whichever you ignore.
