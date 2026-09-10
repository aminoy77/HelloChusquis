# Command pattern

- Command encapsulates requests as objects with execute (and undo) operations.
- Undo/redo stacks store inverse commands for editors and tools.
- Macro commands compose primitives into scriptable batches.
- Job queues persist commands for retry across crashes.
- Receivers perform work; invokers schedule; clients construct — keep roles split.
- Idempotent commands survive at-least-once delivery safely.
- Serialize commands (not closures) for durable outbox patterns.
- CLI parsers map verbs to command objects uniformly.
- Audit logs fall out free when every mutation is a command object.
- State machines pair with commands to gate legal transitions.
