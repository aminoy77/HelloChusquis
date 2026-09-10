# WebSockets

- WebSockets upgrade HTTP to persistent bidirectional channels (`ws://`, `wss://`).
- `new WebSocket(url)` connects; `onmessage` handles frames as they arrive.
- Use `wss://` in production; plain `ws://` leaks content like HTTP.
- Heartbeat pings detect dead peers behind silent NAT timeouts.
- Reconnect with backoff plus server-side session resume for robustness.
- Socket.IO falls back to polling where raw sockets are blocked.
- Broadcast hubs (Redis pub/sub) fan out multi-server socket fleets.
- Backpressure (bounded queues) protects servers from fast publishers.
- Authenticate during handshake; tokens in URLs leak to logs otherwise.
- Close codes (1000 normal, 1011 errors) diagnose drops precisely.
