# Node.js runtime

- Node.js runs JavaScript on V8 outside browsers with OS access.
- `node script.js` executes files; `node --watch` restarts on edits.
- Event loop phases (timers, poll, check) schedule callbacks cooperatively.
- Single-threaded JS plus libuv threadpool balances I/O against CPU work.
- `process.env` reads configuration; `process.exit(code)` sets shell status.
- Built-ins (`fs/promises`, `path`, `os`) cover files and system without deps.
- ESM (`import`) is modern Node; `.cjs` preserves legacy CommonJS per file.
- `node --test` runs the built-in test runner without frameworks.
- Worker threads parallelize CPU work shared via `workerData` messaging.
- LTS versions anchor production; Current previews upcoming features.
