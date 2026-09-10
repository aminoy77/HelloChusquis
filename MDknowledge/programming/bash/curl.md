# Bash curl

- In Bash, `curl -sS url` silences progress while still surfacing errors.
- In Bash, `curl -o file` saves bodies and `-O` keeps the remote filename.
- In Bash, `-w '%{http_code}'` prints statuses for script assertions.
- In Bash, `-H 'Authorization: Bearer TOKEN'` attaches auth headers to requests.
- In Bash, `-d 'a=1'` POSTs form data; `-d @file.json` with content-type sends JSON.
- In Bash, `-X PUT/DELETE` selects methods beyond GET and POST explicitly.
- In Bash, `--max-time 30` bounds hung transfers instead of waiting forever.
- In Bash, `-L` follows redirects that APIs and shorteners commonly return.
- In Bash, `-f` fails on HTTP errors so scripts detect 4xx/5xx via exit codes.
- In Bash, `--retry 3` resends transient failures with backoff for flaky endpoints.
