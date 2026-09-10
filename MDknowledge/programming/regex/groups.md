# Regex groups

- In regex, `(...)` captures numbered groups retrievable as `\1`, `\2` or named via `(?<name>...)`.
- In regex, `(?:...)` groups without capturing, keeping numbering stable and matching fast.
- In regex, named groups `(?<year>\d{4})` document intent and survive pattern edits.
- In regex, backreferences like `(\w+) \1` detect doubled words in prose.
- In regex, alternation binds loosest: `^ab|cd$` means `(^ab)|(cd$)` unless grouped.
- In regex, nested groups number by opening-parenthesis order from the left.
- In regex, atomic groups `(?>...)` (where supported) block backtracking for speed.
- In regex, branch reset `(?|...)` renumbers alternatives from one in PCRE flavors.
- In regex, `re.Match.groups()` returns all captures and `.groupdict()` the named ones in Python.
- In regex, non-participating groups yield None/null — guard before use.
