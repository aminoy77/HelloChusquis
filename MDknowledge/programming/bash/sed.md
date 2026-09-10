# Bash sed

- In Bash, `sed 's/old/new/g'` substitutes all occurrences per line of stream text.
- In Bash, `sed -n '10,20p'` prints only lines 10-20 for targeted inspection.
- In Bash, `sed -i.bak 's/x/y/' file` edits in place keeping a backup copy.
- In Bash, `sed '/pattern/d'` deletes matching lines from the stream.
- In Bash, `&` in replacements replays the whole match without retyping it.
- In Bash, capture groups `\(..\)` plus `\1` rearrange matched segments.
- In Bash, alternate delimiters (`s|a/b|c|`) avoid leaning toothpicks in paths.
- In Bash, `-E` enables extended regex for `+`, `?`, and `|` without escapes.
- In Bash, `sed 's/$/;/'` appends terminators to every line uniformly.
- In Bash, prefer `awk` over sed once fields, not lines, drive the logic.
