# MVC and layered architecture

- MVC splits Model (state), View (rendering), and Controller (input) concerns.
- Thin controllers delegate to services; fat models or services hold logic.
- MVVM binds views to view-models declaratively in UI frameworks.
- Layered builds (API → service → repository) isolate change blast radius.
- Dependency rule: inner layers never import outer ones.
- DTOs cross boundaries so internals stay refactorable.
- Ports-and-adapters (hexagonal) frame the domain with swappable infrastructure.
- Feature folders group vertical slices over horizontal technical layers.
- Each layer gets its own tests; skip-through testing rots boundaries.
- Start monolithic-modular; extract services only at proven pain.
