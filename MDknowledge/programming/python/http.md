# Python http modules

- In Python, `urllib.request.urlopen(url, timeout=10)` fetches URLs with only the standard library.
- In Python, `http.client.HTTPConnection` offers low-level request control when urllib is too coarse.
- In Python, the third-party `httpx`/`requests` libraries simplify sessions, retries, and timeouts.
- In Python, `http.HTTPStatus.OK` names status codes readably instead of magic numbers.
- In Python, `http.server` serves directories for local testing, never for production traffic.
- In Python, always set timeouts on network calls; hanging sockets stall whole programs.
- In Python, `urllib.parse.urlparse` splits URLs and `urlencode` builds query strings safely.
- In Python, `mimetypes.guess_type(path)` maps filenames to Content-Type headers.
- In Python, validate TLS by default; disabling verification invites interception.
- In Python, `json()`-decode HTTP bodies defensively with size caps on untrusted responses.
