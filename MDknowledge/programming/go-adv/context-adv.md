# Go context advanced (example)

- `context.WithDeadline` plus `AfterFunc` schedule cancellation cleanups.
- Propagate contexts through queues/workers, not just RPC handlers.
- `context.Cause` (1.21+) distinguishes cancellation reasons precisely.
- Store request IDs (not sessions) via `WithValue` sparingly.
- Timeouts compose: innermost deadline wins across nested calls.
- Tests inject canceled contexts asserting early-exit behavior.
- Never ignore `ctx.Done()` in loops polling external systems.
- Graceful shutdown threads one root context through whole servers.
- Metrics tag spans with trace IDs extracted from contexts.
- Nil contexts panic; default to `Background()` at boundaries.
