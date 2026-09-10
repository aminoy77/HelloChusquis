# Security headers

- `Content-Security-Policy` whitelists script/style/image sources against XSS.
- `Strict-Transport-Security` (HSTS) pins HTTPS with includeSubDomains and preload.
- `X-Content-Type-Options: nosniff` stops MIME-sniffing drive-bys.
- `X-Frame-Options: DENY` (or frame-ancestors) blocks clickjacking iframes.
- `Referrer-Policy: no-referrer` (or strict) limits URL leakage to third parties.
- `Permissions-Policy` disables camera/mic/geolocation attack surface by default.
- `Cross-Origin-Opener/Embedder-Policy` isolate documents for Spectre-class defenses.
- Report-only modes (`-Report-Only`) trial policies without breaking users.
- Security.txt (`/.well-known/`) advertises disclosure contacts to researchers.
- Scan headers in CI (securityheaders.com, custom checks) to stop regressions.
