# Python metaclasses (example)

- Metaclasses customize class creation via `__new__`/`__init__` on `type` subclasses.
- `__init_subclass__` hooks subclass creation more simply in most cases.
- Registries (plugins, ORMs) auto-collect subclasses through metaclasses.
- ABCs plus `@abstractmethod` enforce interfaces without full metaclasses.
- Dataclasses/Enums are metaclass-powered conveniences, not magic.
- `__call__` on metaclasses intercepts instantiation (singletons, caching).
- Conflicting metaclasses multiply-inherit painfully — avoid the combination.
- 99 percent of metaclass uses simplify to decorators or class hooks.
- Frameworks (Django models) justify metaclasses; applications rarely do.
- Document metaclass behavior heavily; readers cannot infer it locally.
