# State machines

- State machines model behavior as states plus guarded transitions on events.
- Explicit machines beat boolean-flag soup past two flags.
- Enumerate states and events in one table before coding transitions.
- Hierarchical states (HSM) share transitions across nested modes.
- Guards (conditions) plus actions (effects) keep transitions declarative.
- XState/statecharts tooling visualizes and tests machine definitions.
- Persist state, not flags, for resumable workflows and sagas.
- Invalid transitions should error loudly, never silently no-op.
- Model UI flows (idle/loading/error) as machines to kill impossible states.
- Test every transition, including self-loops and guard boundaries.
