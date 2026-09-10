# Bash ls and navigation

- In Bash, `ls -la` lists all entries with permissions, sizes, and timestamps.
- In Bash, `ls -lh` renders human sizes (K/M/G) instead of raw byte counts.
- In Bash, `ls -lt` sorts by modification time, newest first, for recent work.
- In Bash, `cd -` returns to the previous directory instantly.
- In Bash, `pushd`/`popd` stack directories for multi-stop shell tours.
- In Bash, `~` expands to home and `~user` to another user's home directory.
- In Bash, `ls *.md` globs matches in-shell before `ls` ever runs.
- In Bash, `ls -R` recurses trees; pipe to `less` for paging long output.
- In Bash, `stat file` reports inode, permissions, and all three timestamps precisely.
- In Bash, `realpath file` (or `readlink -f`) resolves symlinks to absolute paths.
