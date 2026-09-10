# Bash sort and uniq

- In Bash, `sort file` orders lines byte-wise; `-n` sorts numerically, `-h` human sizes.
- In Bash, `sort -u` dedupes while sorting in a single pass.
- In Bash, `sort -t, -k2` keys sorting on CSV fields instead of whole lines.
- In Bash, `sort -r` reverses order for newest-first or biggest-first views.
- In Bash, `uniq` collapses only adjacent duplicates, so always `sort` first.
- In Bash, `uniq -c` prefixes repetition counts for frequency analysis.
- In Bash, `uniq -d` shows only duplicated lines and `-u` only unique ones.
- In Bash, `sort --parallel=4 -S 50%` speeds giant sorts with cores and memory.
- In Bash, `LC_ALL=C sort` standardizes byte ordering across locales.
- In Bash, `shuf file` randomizes lines for sampling and quiz generation.
