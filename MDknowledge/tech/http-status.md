# HTTP status codes

- HTTP 200 OK means the request succeeded with a response body.
- HTTP 201 Created confirms a new resource exists, usually with its Location.
- HTTP 204 No Content succeeds deliberately without a body.
- HTTP 301 Moved Permanently redirects with caching; 302 Found is temporary.
- HTTP 304 Not Modified answers conditional GETs, saving bandwidth.
- HTTP 400 Bad Request flags malformed client input to fix and retry differently.
- HTTP 401 Unauthorized demands authentication credentials first.
- HTTP 403 Forbidden authenticates but refuses permission for this resource.
- HTTP 404 Not Found means no resource at the URL, whatever the reason.
- HTTP 409 Conflict signals state clashes like duplicate keys or edit races.
- HTTP 422 Unprocessable Entity passes syntax but fails semantic validation.
- HTTP 429 Too Many Requests rate-limits; honor Retry-After before retrying.
- HTTP 500 Internal Server Error blames the server; clients may retry idempotent calls.
- HTTP 503 Service Unavailable marks temporary overload or maintenance windows.
