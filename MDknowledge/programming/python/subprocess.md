# Python subprocess module

- In Python, `subprocess.run(['git', 'status'], capture_output=True, text=True)` runs commands safely without a shell.
- In Python, pass argument lists, never `shell=True` with untrusted input, to avoid injection.
- In Python, `check=True` raises `CalledProcessError` on nonzero exits instead of silent failure.
- In Python, `result.stdout` and `result.stderr` hold captured text when `capture_output` is set.
- In Python, `timeout=30` kills hung commands via `TimeoutExpired` instead of hanging forever.
- In Python, `subprocess.Popen` streams interactively when `run` is too coarse.
- In Python, `env={...}` replaces the child environment; merge `os.environ` to extend it.
- In Python, `cwd=` sets the child's working directory without process-wide `os.chdir`.
- In Python, `input=` feeds stdin bytes or text to the child process directly.
- In Python, prefer `shlex.join(cmd)` for logging commands safely and readably.
