# Hashing

- Hash tables average O(1) insert/lookup by bucketing keys on hash codes.
- Collisions resolve by chaining (lists) or open addressing (probing).
- Load factor (entries/buckets) triggers resizes past ~0.7 for open addressing.
- Good hashes avalanche: one input bit flips half the output bits.
- Cryptographic hashes (SHA-256) resist preimages; non-crypto (FNV, xxHash) prioritize speed.
- Hash flooding attacks degrade naive tables; randomized seeds (SipHash) defend them.
- Consistent hashing remaps minimally when nodes join or leave clusters.
- Bloom filters test set membership with tunable false positives and zero false negatives.
- Content hashes (git, IPFS) deduplicate and verify data by digest.
- Equality must agree with hashing: equal objects need equal hash codes.
