# Python re module

- In Python, `re.search(pattern, text)` finds the first match anywhere in the string.
- In Python, `re.match` anchors implicitly at the start; prefer `re.fullmatch` for whole-string checks.
- In Python, `re.findall` returns all non-overlapping matches as strings or tuples.
- In Python, `re.sub(pattern, repl, text)` replaces matches; backreferences like `\1` reuse groups.
- In Python, compile hot patterns once with `re.compile` and reuse the object.
- In Python, named groups `(?P<name>...)` document captures retrievable via `m.group('name')`.
- In Python, `re.split` divides text on pattern matches, keeping separators with capture groups.
- In Python, flags `re.IGNORECASE`, `re.MULTILINE`, and `re.DOTALL` adjust matching behavior.
- In Python, raw strings `r'\d+'` avoid doubling backslashes in patterns.
- In Python, `re.VERBOSE` allows whitespace and `#` comments inside complex patterns.
