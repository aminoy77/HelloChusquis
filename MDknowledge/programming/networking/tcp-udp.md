# TCP vs UDP

- TCP guarantees ordered reliable streams via handshakes, ACKs, and retransmits.
- UDP fires datagrams without guarantees, minimizing latency and overhead.
- TCP's three-way handshake (SYN, SYN-ACK, ACK) opens connections statefully.
- UDP suits live media, gaming, and DNS where stale data beats late data.
- TCP congestion control (slow start, AIMD) shares bandwidth fairly across flows.
- Head-of-line blocking stalls TCP streams on single losses; QUIC fixes it atop UDP.
- Ports multiplex services per host: TCP/80 and UDP/80 are distinct sockets.
- Sockets bind IP plus port; `listen`/`accept` (TCP) versus fire-and-forget (UDP).
- MTU limits (~1500B Ethernet) fragment oversized datagrams, hurting UDP designs.
- Choose TCP by default; reach for UDP with measured latency justification.
