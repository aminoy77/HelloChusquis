# Dependency injection

- Dependency injection passes collaborators in instead of constructing them inside.
- Constructor injection suits required deps; setters suit optional reconfiguration.
- Interfaces (or protocols) as parameter types enable test doubles.
- Composition roots wire graphs once at startup, not scattered `new` calls.
- Containers automate wiring; manual construction suffices for small apps.
- Singletons, scoped, and transient lifetimes must be chosen deliberately.
- Captive dependencies (long-lived holding short-lived) cause stale-state bugs.
- Constructor over-injection (7+ params) signals a class doing too much.
- Mockist tests verify collaborations; classicist tests verify outcomes — mix wisely.
- DI shines at seams (I/O, time, randomness); pure logic needs none.
