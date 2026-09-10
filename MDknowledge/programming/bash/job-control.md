# Bash job control

- In Bash, `Ctrl-Z` suspends foreground jobs; `bg` resumes them backgrounded.
- In Bash, `fg %1` foregrounds job 1 for interactive control.
- In Bash, `jobs -l` lists PIDs alongside job numbers for signaling.
- In Bash, `kill %1` signals by job spec instead of raw PID.
- In Bash, `disown` detaches jobs from shell exit cleanup.
- In Bash, `wait` blocks until background jobs complete for sequencing.
- In Bash, `set -m` enables job control in non-interactive scripts explicitly.
- In Bash, `trap` handlers clean temp files on signals including TERM.
