# Singleton pattern

- Singleton guarantees one instance with global access via a controlled factory.
- Lazy initialization defers creation cost until first use.
- Singletons hide dependencies and resist testing; prefer injection where possible.
- Thread-safe singletons need locks or language-level guarantees (module scope).
- Python modules are natural singletons without extra machinery.
- Enum singletons (Java) survive serialization and reflection attacks.
- Registry/multiton variants map keys to one-instance-per-key managers.
- Global mutable singletons complicate parallel tests with shared state.
- Monostate (Borg) shares state across instances as a flexible alternative.
- Document why singularity is required, not merely convenient.
