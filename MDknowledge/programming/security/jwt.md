# JWT essentials

- JWTs carry header, payload, and signature segments dot-joined and base64url-encoded.
- Verify signatures with the issuer's keys (JWKS) before trusting any claim.
- Check `exp`, `nbf`, `iss`, and `aud` claims — signature alone is insufficient.
- Keep payloads small and non-sensitive; JWTs are signed, not encrypted, by default.
- Short expirations plus refresh rotation bound stolen-token damage.
- `alg: none` and algorithm-confusion attacks must be explicitly rejected in libraries.
- JWE encrypts tokens when payloads cannot be public.
- Revocation needs denylists or short lifetimes since JWTs are stateless.
- Rotate signing keys with overlapping `kid` support for zero-downtime swaps.
- Prefer opaque session tokens when revocation agility outweighs statelessness.
