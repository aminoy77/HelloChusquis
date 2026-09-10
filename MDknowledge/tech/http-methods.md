# HTTP methods

- GET retrieves representations and must not change server state.
- POST submits data for processing, creating subordinates in REST designs.
- PUT replaces whole resources idempotently at known URLs.
- PATCH applies partial updates idempotently when designed so.
- DELETE removes resources and should be idempotent on repeats.
- HEAD fetches headers only for existence and freshness checks.
- OPTIONS discovers allowed methods and CORS permissions preflight.
- Safe methods (GET, HEAD, OPTIONS) never mutate; idempotent ones repeat safely.
- POST-redirect-GET prevents duplicate form submissions on browser refresh.
- Method overriding (`X-HTTP-Method-Override`) tunnels verbs through limited clients.
