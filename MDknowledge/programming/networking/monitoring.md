# Network monitoring

- Ping tests reachability; MTR blends ping plus traceroute for path fault location.
- SNMP polls device counters; exporters (Prometheus) modernize the same idea.
- Flow records (NetFlow/sFlow) reveal who-talks-to-whom without full capture.
- Packet captures (tcpdump/Wireshark) dissect the exact failing exchange.
- Synthetic probes (uptime checks) catch outages before users report them.
- Bandwidth (capacity) differs from throughput (achieved) differs from latency.
- Bufferbloat inflates latency under load; smart queueing (fq_codel) tames it.
- Baseline normal traffic so anomalies stand out during incidents.
- Alert on symptoms (error budgets) not just causes (CPU) to page usefully.
- Retain captures briefly; full packets are a privacy liability at rest.
