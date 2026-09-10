# Publish-subscribe

- Pub-sub decouples publishers from subscribers via topic routing.
- Topics fan out; queues load-balance — choose by delivery intent.
- At-least-once delivery plus idempotent handlers is the robust default.
- Retention windows (Kafka logs) allow replays that queues cannot.
- Dead-letter queues quarantine poison messages for inspection.
- Schema registries version event payloads compatibly.
- Ordering holds per partition/key, rarely global — design accordingly.
- Backpressure (bounded buffers, load shedding) protects subscribers from floods.
- Observability (lag metrics, trace ids) makes async flows debuggable.
- Prefer request-reply for queries; events for facts that happened.
