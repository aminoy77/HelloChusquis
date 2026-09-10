# Hashing basics

- Hash functions map arbitrary input to fixed-size digests deterministically.
- SHA-256 outputs 256 bits and resists preimage and collision attacks practically.
- MD5 and SHA-1 are broken for security; use them only for non-adversarial checksums.
- Salts randomize password hashes so identical passwords differ per user.
- bcrypt, scrypt, and Argon2 tune computational cost against brute-force cracking.
- Key stretching repeats hashing to slow attackers while staying fast for logins.
- HMAC keyed hashes authenticate messages with shared secrets.
- Content addressing (git, IPFS) names blobs by hash for deduplication and integrity.
- Hash maps average O(1) lookup by bucketing keys on their hash codes.
- Checksums detect corruption in transit, never malicious tampering alone.
