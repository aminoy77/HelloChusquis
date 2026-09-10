# JavaScript fetch

- In JavaScript, `fetch(url)` resolves on any HTTP status; check `res.ok` before parsing.
- In JavaScript, `await res.json()` parses bodies; pair with `Content-Type: application/json` on sends.
- In JavaScript, POST JSON via `fetch(url, {method: 'POST', headers, body: JSON.stringify(data)})`.
- In JavaScript, network failures reject fetch but HTTP 4xx/5xx resolve normally.
- In JavaScript, `AbortController` plus `signal` cancels in-flight requests on navigation.
- In JavaScript, `new URLSearchParams(obj)` builds encoded query strings safely.
- In JavaScript, `FormData` posts multipart forms including files without manual boundaries.
- In JavaScript, CORS errors surface as opaque TypeErrors; fix server headers, not client code.
- In JavaScript, cache GETs with `cache: 'force-cache'` or explicit service-worker strategies.
- In JavaScript, always bound fetch with timeouts via AbortController to avoid hung UI.
