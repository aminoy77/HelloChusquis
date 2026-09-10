# C debugging with gdb

- In C, compile with `-g -O0` for accurate gdb line numbers and variable values.
- In C, `gdb ./prog` plus `run args` starts sessions; `break file.c:42` sets breakpoints.
- In C, `next` steps over calls while `step` descends into functions.
- In C, `print expr` evaluates variables and `display expr` reprints each stop.
- In C, `backtrace` shows the call stack when crashes land in strange frames.
- In C, `watch var` breaks on writes to catch memory corruption sources.
- In C, `continue` resumes to the next breakpoint or crash.
- In C, core dumps plus `gdb ./prog core` debug crashes post-mortem.
- In C, `-fsanitize=address,undefined` catches bugs faster than manual gdb sessions.
- In C, `valgrind --leak-check=full` reports leaks with allocation stacks.
