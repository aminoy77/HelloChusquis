# Web workers

- Web workers run scripts off the main thread for responsive UIs.
- `new Worker('w.js')` spawns; `postMessage`/`onmessage` pass data (structured-cloned).
- Workers lack DOM access; they compute, fetch, and return results.
- SharedWorkers share one instance across same-origin tabs.
- Service workers proxy network for offline support and push.
- Transferables (`buffer, [buffer]`) move memory zero-copy to workers.
- Inline workers via Blob URLs avoid extra files for tiny tasks.
- Terminate idle workers; each costs megabytes of memory.
- Comlink-style RPC wrappers hide message plumbing ergonomically.
- Debug workers in devtools' dedicated threads panel.
