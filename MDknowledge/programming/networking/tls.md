# TLS essentials

- TLS negotiates cipher suites then encrypts with ephemeral session keys (forward secrecy).
- Certificates bind domain names to public keys via trusted certificate authorities.
- Let's Encrypt issues free automated certificates renewing every 90 days.
- TLS 1.2 is the floor; TLS 1.0/1.1 are broken and must be disabled.
- Certificate chains validate leaf through intermediates to roots in trust stores.
- Hostname verification (not just chain validity) stops most interception attacks.
- HSTS headers pin HTTPS so first-visit downgrades cannot strip encryption.
- OCSP stapling proves non-revocation without leaking browsing to responders.
- Mutual TLS authenticates clients with certificates instead of passwords.
- Expiry monitoring prevents the classic outage: an unnoticed lapsed certificate.
