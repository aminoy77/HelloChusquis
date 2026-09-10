# HTTP/2 and HTTP/3

- HTTP/2 multiplexes streams over one TCP connection, killing head-of-line delays per request.
- HTTP/2 header compression (HPACK) shrinks repetitive cookie-laden headers.
- HTTP/2 server push is deprecated; preload hints (`103 Early Hints`) replaced it.
- HTTP/2 mandates TLS in browsers though the spec allows cleartext.
- HTTP/3 runs over QUIC (UDP) surviving network switches (Wi-Fi to cellular) gracefully.
- HTTP/3's 0-RTT resumption reconnects faster at replay-attack caution cost.
- Prioritization and_server push complexities make HTTP/2 tuning an expert sport.
- Most CDNs negotiate h2/h3 automatically; origin support just needs current servers.
- Debug with protocol indicators (`:authority` pseudo-headers) in devtools.
- Adoption is transparent to well-written HTTP/1.1 apps in most frameworks.
