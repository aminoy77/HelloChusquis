# Bash find

- In Bash, `find . -name '*.tmp'` locates by glob pattern recursively.
- In Bash, `-type f`/`-type d` restrict matches to files or directories.
- In Bash, `-mtime -7` finds content modified within the last week.
- In Bash, `-size +100M` surfaces disk hogs above the threshold.
- In Bash, `-print` previews before destructive `-delete` in the same command.
- In Bash, `-exec cmd {} \;` runs per file; `+` batches arguments efficiently.
- In Bash, `-maxdepth 2` bounds recursion depth for focused searches.
- In Bash, `-empty` finds zero-byte files and vacant directories for cleanup.
- In Bash, `-newer ref` selects files changed since a reference file.
- In Bash, `find . -name .git -prune` skips VCS metadata during sweeps.
