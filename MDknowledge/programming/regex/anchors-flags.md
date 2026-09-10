# Regex anchors and flags

- In regex, `^` and `$` anchor to string (or line, in multiline mode) start and end.
- In regex, `\b` matches word boundaries, ideal for whole-word search like `\bcat\b`.
- In regex, `\A` and `\Z` anchor to absolute string ends regardless of multiline mode.
- In regex, case-insensitive matching comes from flags (`i`) rather than `[aA]` classes.
- In regex, multiline mode makes `^`/`$` work per line for log and file processing.
- In regex, dot-all/single-line mode lets `.` cross newlines for multi-line blocks.
- In regex, `re.fullmatch` (Python) and `\A...\Z` both enforce whole-string matches.
- In regex, `^` inside `[^...]` negates the class instead of anchoring — context decides.
- In regex, lookahead `(?=...)` and lookbehind `(?<=...)` assert without consuming characters.
- In regex, negative lookahead `(?!...)` forbids patterns like weak passwords compactly.
