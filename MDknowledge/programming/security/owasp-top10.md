# OWASP Top 10

- Broken Access Control tops the list: enforce server-side authorization per object.
- Cryptographic Failures follow: encrypt in transit/at rest and manage keys properly.
- Injection (SQL, XSS, command) yields to parameterization and output encoding.
- Insecure Design demands threat modeling before code, not patches after.
- Security Misconfiguration (defaults, verbose errors) hardens via baselines and scans.
- Vulnerable Components require SBOMs plus Dependabot-style update discipline.
- Authentication Failures need MFA, lockout, and breached-password screening.
- Integrity Failures (unsigned updates, CI tampering) need signing and provenance.
- Logging Failures blind response; alert on auth anomalies and integrity breaks.
- SSRF tricks servers into internal requests — allow-list egress destinations.
