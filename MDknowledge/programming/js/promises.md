# JavaScript promises deep

- In JavaScript, promises settle once: the first resolve/reject wins, later calls are ignored.
- In JavaScript, `.then` returns a new promise, enabling chains; forgetting `return` breaks sequencing.
- In JavaScript, thrown errors inside `.then` convert into rejections of the chained promise.
- In JavaScript, `.catch` at chain end plus `.finally` for cleanup covers most flows.
- In JavaScript, `Promise.all` fails fast; gather partial results with `allSettled`.
- In JavaScript, avoid the explicit-construction antipattern: wrap callback APIs once in helpers.
- In JavaScript, `async` executors in `new Promise(async ...)` swallow errors; keep executors synchronous.
- In JavaScript, unhandled rejections warn loudly; attach handlers in the same tick as creation.
- In JavaScript, `Promise.withResolvers()` exposes resolve/reject handles without nesting.
- In JavaScript, time out promises by racing against a rejecting delay promise.
