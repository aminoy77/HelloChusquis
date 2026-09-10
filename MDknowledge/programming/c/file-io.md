# C file IO

- In C, `fopen(path, "r")` returns NULL on failure; always check before use.
- In C, modes `"r"`, `"w"`, `"a"` read, truncate-write, and append; add `b` for binary.
- In C, `fgets(buf, sizeof buf, f)` reads lines safely where `gets` overflows.
- In C, `fprintf`/`fscanf` format output and parse input with explicit width limits.
- In C, `fread`/`fwrite` move binary blocks; check their return counts for short IO.
- In C, `fseek`/`ftell` reposition and report offsets in seekable files.
- In C, `fclose` flushes buffers; skipped closes lose trailing output.
- In C, `perror("open")` prints the human reason after failed syscalls.
- In C, `errno` captures failure codes; read it before any other call clobbers it.
- In C, `stdin`/`stdout`/`stderr` are the standard streams available without opening.
