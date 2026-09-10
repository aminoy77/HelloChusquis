# Bash awk

- In Bash, `awk '{print $1}'` prints the first whitespace-separated field per line.
- In Bash, `-F,` switches the delimiter to commas for CSV-ish input.
- In Bash, `awk '$3 > 100'` filters rows on field conditions inline.
- In Bash, `NR` counts all lines and `FNR` restarts per file across inputs.
- In Bash, `BEGIN {sum=0} {sum+=$1} END {print sum}` aggregates columns idiomatically.
- In Bash, `awk -F: '{print $1}' /etc/passwd` extracts usernames from system files.
- In Bash, `length($0) > 80` flags overlong lines during lint passes.
- In Bash, associative arrays `count[$1]++` tally categories in one pass.
- In Bash, `printf '%-20s %d\n', $1, $2` formats aligned reports portably.
- In Bash, `next` skips to the following record, structuring multi-rule scripts.
