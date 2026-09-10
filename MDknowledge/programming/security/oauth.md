# OAuth 2 and OpenID Connect

- OAuth 2 delegates authorization without sharing passwords with third parties.
- Authorization Code + PKCE is the mandatory flow for public clients (SPAs, mobile).
- Implicit and password grants are legacy and must not be built anew.
- ID tokens (OIDC) authenticate users; access tokens authorize API calls — don't confuse them.
- Validate issuer, audience, expiry, and signatures on every token server-side.
- Refresh tokens rotate (one-time use) to bound theft windows.
- Scopes follow least privilege; request increments, not blanket access.
- Redirect URIs must be exact-registered to block code interception.
- State + nonce parameters defeat CSRF and replay on login round-trips.
- Store tokens in httpOnly secure contexts, never localStorage for sensitive scopes.
