# Bash redirection deep

- In Bash, `2>&1` merges stderr into stdout for unified logs.
- In Bash, `&>` redirects both streams tersely in modern Bash.
- In Bash, `cmd <<< 'str'` feeds here-strings without temp files.
- In Bash, `cmd <(other)` process substitution fakes files from commands.
- In Bash, `> file` truncates; `>| file` overrides noclobber protections.
- In Bash, `exec >log 2>&1` redirects whole scripts persistently.
- In Bash, `/dev/null` discards; `/dev/stderr` addresses error streams directly.
- In Bash, order matters: `2>&1 >f` differs from `>f 2>&1` subtly.
