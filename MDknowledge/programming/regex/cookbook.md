# Regex cookbook

- In regex, `^[\w.-]+@[\w.-]+\.\w+$` approximates emails; prefer validators for real checks.
- In regex, `^https?://[^\s/$.?#].[^\s]*$` sketches URL matching before using a parser.
- In regex, `\d{4}-\d{2}-\d{2}` finds ISO dates; validate month/day ranges separately.
- In regex, `^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,}$` enforces mixed password classes.
- In regex, `#,?(\d{3})` style grouping parses thousands separators in numbers.
- In regex, `\s+` collapses whitespace runs when normalizing pasted text.
- In regex, `^\s*$` detects blank lines during file cleanup passes.
- In regex, `(['"])(?:(?!\1).)*\1` matches quoted strings with either quote style.
- In regex, `\b(https?://\S+)` extracts raw URLs from prose reliably.
- In regex, always test cookbook patterns against adversarial inputs before shipping.
