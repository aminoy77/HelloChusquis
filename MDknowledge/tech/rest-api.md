# REST API principles

- REST addresses resources with nouns (`/orders/42`) not verbs in URLs.
- GET reads, POST creates, PUT/PATCH update, DELETE removes in REST conventions.
- GET, PUT, and DELETE should be idempotent: repeats equal one call.
- POST creates subordinates and is neither safe nor idempotent by default.
- Status codes report outcomes: 2xx success, 4xx client errors, 5xx server faults.
- Version APIs (`/v1/...`) so breaking changes never ambush existing clients.
- Paginate collections (`?page=&limit=`) with total counts or cursor tokens.
- Filter, sort, and search via query params, never new endpoints per combination.
- Authenticate with tokens (Bearer) over TLS; never in URL query strings.
- Document with OpenAPI so clients generate SDKs and tests automatically.
