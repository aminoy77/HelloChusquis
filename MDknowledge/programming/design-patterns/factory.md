# Factory patterns

- Simple factories centralize construction logic behind one function.
- Factory methods defer instantiation to subclasses for framework hooks.
- Abstract factories produce families (dark/light widgets) interchangeably.
- Builders assemble complex objects step by step with readable fluent calls.
- Prototypes clone templates instead of constructing from scratch.
- Dependency injection containers generalize factories with lifetime management.
- Named constructors (`from_json`) beat boolean-flagged constructors for clarity.
- Registries mapping names to classes enable plugin-style extensibility.
- Factories isolate `new` calls so tests can substitute fakes at one seam.
- Over-factorizing trivial construction adds indirection without benefit.
