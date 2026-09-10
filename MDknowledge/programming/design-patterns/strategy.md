# Strategy pattern

- Strategy swaps algorithms behind one interface at runtime.
- Comparators, sort keys, and pricing rules are everyday strategies.
- Composition with strategies beats subclass explosions for behavior variants.
- First-class functions often replace strategy classes in modern languages.
- Registry maps select strategies by name for config-driven behavior.
- Validate strategy preconditions at selection time, not deep in execution.
- Stateless strategies share safely; stateful ones need per-use instances.
- Policy objects bundle related strategies (tax + shipping + discount) coherently.
- Testing strategies in isolation beats end-to-end coverage of every combination.
- Name strategies by intent (AggressiveRetry), not mechanism.
