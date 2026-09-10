# Python io module

- In Python, `io.StringIO()` is an in-memory text file for building or capturing output.
- In Python, `io.BytesIO(b'data')` is the binary counterpart for protocol work.
- In Python, `io.open` is the builtin `open`; both accept `encoding` and `newline` controls.
- In Python, `.getvalue()` retrieves the full StringIO/BytesIO contents without rewinding.
- In Python, `.seek(0)` rewinds streams so a second reader sees everything.
- In Python, `io.TextIOWrapper` layers text decoding over raw binary streams.
- In Python, `io.BufferedReader` adds efficient chunked reads to raw streams.
- In Python, redirect output in tests with `contextlib.redirect_stdout(io.StringIO())`.
- In Python, always `close()` or use `with` blocks so buffers flush completely.
- In Python, `io.DEFAULT_BUFFER_SIZE` hints the chunk size for custom stream classes.
