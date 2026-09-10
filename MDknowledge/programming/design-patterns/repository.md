# Repository pattern

- Repositories mediate domain code and persistence behind collection-like APIs.
- Callers see `find/add/remove`, never SQL or HTTP details.
- One repository per aggregate root keeps transaction boundaries clear.
- Specification objects parameterize queries without leaking query languages.
- Unit of work batches repository changes into atomic commits.
- In-memory fakes make domain tests fast and deterministic.
- Pagination belongs in repository signatures for large collections.
- Map persistence exceptions to domain errors at the boundary.
- Repositories return domain entities, never ORM rows or DTOs.
- CQRS splits read models from write repositories at scale.
