# Bash viewing text

- In Bash, `less file` pages with search (`/`) without loading everything into memory.
- In Bash, `head -n 20` and `tail -n 20` preview file edges quickly.
- In Bash, `tail -f log` follows live appends; `--retry` survives rotation gaps.
- In Bash, `cat file` dumps small files; prefer pagers beyond one screen.
- In Bash, `bat` adds syntax highlighting and line numbers over plain `cat`.
- In Bash, `wc -l file` counts lines and `wc -w` counts words for size checks.
- In Bash, `sort file | uniq -c | sort -nr` ranks duplicate lines by frequency.
- In Bash, `cut -d, -f1,3` slices delimited columns without heavier tools.
- In Bash, `column -t` aligns ragged output into readable tables.
- In Bash, `diff -u old new` shows unified changes before overwriting files.
