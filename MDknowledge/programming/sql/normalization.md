# Database normalization

- 1NF: atomic values per cell, no repeating groups or arrays in columns.
- 2NF: non-key attributes depend on whole composite keys, not parts.
- 3NF: no transitive dependencies — facts depend on keys, the whole key.
- BCNF tightens 3NF for overlapping candidate-key edge cases.
- Denormalize deliberately for read speed (counts, caches) with sync strategies.
- Join tables resolve many-to-many relations without duplication.
- Surrogate keys (serial/UUID) stabilize joins versus natural-key churn.
- Over-normalization (EAV anti-pattern) trades queries for flexibility painfully.
- Document intentional denormalization so future devs preserve invariants.
- Measure before normalizing hot paths; theory serves latency, not vice versa.
