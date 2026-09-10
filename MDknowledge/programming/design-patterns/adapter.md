# Adapter pattern

- Adapters translate incompatible interfaces so existing code interoperates.
- Voltage converters, ORM dialects, and API shims are physical and digital adapters.
- Wrap third-party APIs behind adapters to contain vendor lock-in.
- Two-way adapters bridge both directions when migration runs in parallel.
- Facade simplifies subsystems; adapter reconciles mismatched ones.
- Anticorruption layers (DDD) adapt legacy models to new bounded contexts.
- Version adapters translate v1 payloads to v2 schemas during rollouts.
- Keep adapters thin: logic belongs in domain code, not translation glue.
- Test adapters against recorded fixtures of the foreign interface.
- Retire adapters once migrations complete; they accrue as debt otherwise.
