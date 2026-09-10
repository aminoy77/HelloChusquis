# Bash grep

- In Bash, `grep 'pattern' file` prints matching lines with case-sensitive matching.
- In Bash, `grep -r` recurses directories and `-n` prefixes line numbers.
- In Bash, `grep -i` ignores case and `-v` inverts to non-matching lines.
- In Bash, `grep -E` enables extended regex (`+`, `?`, `|`, groups) without backslashes.
- In Bash, `grep -F` matches fixed strings literally, fastest for error codes.
- In Bash, `grep -c` counts matches and `-l` lists only filenames containing hits.
- In Bash, `grep -A3 -B3` prints context lines around each match for readability.
- In Bash, `grep --include='*.py'` scopes recursive searches to relevant files.
- In Bash, `grep -q` silences output for pure condition checks in scripts.
- In Bash, `rg` (ripgrep) respects `.gitignore` and outruns grep on big trees.
