# Stacks and queues

- Stacks are LIFO: push/pop power undo, backtracking, and expression parsing.
- Queues are FIFO: enqueue/dequeue schedule breadth-first work fairly.
- Deques add O(1) operations at both ends for sliding windows and palindromes.
- Priority queues pop extremes first, driving schedulers and Dijkstra.
- Two stacks implement a queue amortized O(1); two queues make a clumsy stack.
- Monotonic stacks solve next-greater-element in linear time.
- Circular buffers bound queues in fixed memory for streaming telemetry.
- Call stacks track function frames; overflow signals runaway recursion.
- Message queues decouple producers/consumers across services durably.
- Rate limiters often pair token buckets (queue theory) with fixed windows.
