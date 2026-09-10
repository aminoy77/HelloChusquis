# Go HTTP advanced (example)

- Middleware chains (logging→auth→handler) compose via wrapping functions.
- `http.ServeMux` 1.22 patterns (`GET /u/{id}`) retire most routers.
- Streaming (`Flusher`) pushes SSE/chunked responses incrementally.
- `http.MaxBytesReader` caps upload bodies against abuse.
- Timeouts (`ReadHeaderTimeout`!) blunt Slowloris attacks effectively.
- Graceful `Server.Shutdown(ctx)` drains in-flight requests on deploys.
- `httptest.NewServer` spins real servers for client tests.
- ReverseProxy (`httputil`) builds gateways in stdlib lines.
- HTTP/2 serves automatically over TLS with zero config.
- `http2.ConfigureTransport` tunes pooled client transports explicitly.
