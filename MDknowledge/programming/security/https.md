# HTTPS deployment

- HTTPS authenticates servers and encrypts transit via TLS certificates.
- Redirect all HTTP to HTTPS (301) plus HSTS to kill downgrade paths.
- Automate issuance/renewal (ACME/Let's Encrypt) to end expiry outages.
- Prefer ECDSA certificates for smaller handshakes and faster TLS.
- Enable OCSP stapling for revocation checks without privacy leaks.
- Disable TLS 1.0/1.1 and weak ciphers (RC4, 3DES, export suites).
- Mixed-content (HTTP subresources) breaks padlocks; serve everything TLS.
- Certificate Transparency logs expose misissued certs for your domains.
- Pin public keys (HPKP is dead; use Expect-CT/CT monitoring) cautiously.
- Internal services deserve TLS too; flat-trust LANs betray zero-trust.
