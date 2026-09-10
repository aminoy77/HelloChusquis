# Rust async streams (example)

- Streams (`StreamExt`) generalize iterators across await points.
- `tokio::select!` races branches, cancelling losers automatically.
- `tokio::join!` awaits all branches concurrently collecting tuples.
- `mpsc` channels bound producers/consumers with backpressure naturally.
- `oneshot` returns single values from spawned tasks cleanly.
- `broadcast` fans one sender to many lagging-tolerant receivers.
- `tokio::time::sleep` pauses cooperatively without blocking workers.
- `spawn_blocking` offloads CPU/legacy sync code from async executors.
- `tracing` spans follow async causality better than log lines.
- `#[tokio::test]` runs async unit tests with runtime flavors.
