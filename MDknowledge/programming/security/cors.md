# CORS essentials

- CORS lets servers opt specific origins into cross-origin browser reads.
- `Access-Control-Allow-Origin` with exact origins (never `*` with credentials) gates access.
- Preflight OPTIONS checks non-simple methods/headers before the real request.
- Credentials mode requires explicit origin plus `Allow-Credentials: true`.
- Expose only needed headers via `Access-Control-Expose-Headers`.
- `SameSite` cookies plus CORS form complementary, not redundant, defenses.
- Wildcard subdomains need dynamic origin validation against an allow-list.
- Proxying third-party APIs server-side sidesteps browser CORS entirely.
- Misconfigured `*` with credentials silently fails closed in modern browsers.
- Test from real foreign origins, not just curl, which ignores CORS.
