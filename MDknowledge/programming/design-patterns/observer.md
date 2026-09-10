# Observer pattern

- Observer notifies subscribers on state change without coupling to them.
- Event emitters (Node), signals (Qt/Django), and pub/sub buses implement it.
- Unsubscribe rigorously or listeners leak for the publisher's lifetime.
- Weak references prevent observers from pinning subjects in memory.
- Push models send data; pull models send notifications with query-back.
- Ordering guarantees are usually absent; design subscribers order-independently.
- Synchronous dispatch risks reentrancy when handlers mutate the subject.
- Event sourcing persists the notification log as the system of record.
- Reactive streams (Rx, signals) compose observer chains declaratively.
- Overuse scatters control flow invisibly; prefer explicit calls for core logic.
