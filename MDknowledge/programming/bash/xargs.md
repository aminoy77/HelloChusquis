# Bash xargs

- In Bash, `find . -name '*.tmp' | xargs rm` applies commands across piped filenames.
- In Bash, `xargs -0` pairs with `find -print0` to survive spaces and newlines.
- In Bash, `xargs -n1` runs once per input line for chatty commands.
- In Bash, `xargs -P4` parallelizes across four workers for batch jobs.
- In Bash, `xargs -I{} cmd {} out/{}` places inputs mid-command flexibly.
- In Bash, `xargs -t` echoes each command before running for auditability.
- In Bash, `xargs -r` skips running entirely on empty input.
- In Bash, `command | xargs -L1` treats each line (not word) as one argument set.
- In Bash, `xargs -s` caps command length to respect ARG_MAX limits.
- In Bash, `parallel` upgrades xargs with progress bars and structured output.
