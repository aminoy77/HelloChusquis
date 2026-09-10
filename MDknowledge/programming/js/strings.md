# JavaScript strings

- In JavaScript, template literals `Hello ${name}` interpolate expressions and span lines.
- In JavaScript, `str.length`, `str[i]`, and `str.at(-1)` inspect characters safely.
- In JavaScript, `slice(start, end)` extracts safely; `substring` swaps inverted bounds, so prefer slice.
- In JavaScript, `split(',')` divides and `join(',')` rejoins; trim first with `trim()`.
- In JavaScript, `includes`, `startsWith`, and `endsWith` test content without index math.
- In JavaScript, `replace(a, b)` swaps the first hit only; `replaceAll` or `/g` regex swaps all.
- In JavaScript, `toLowerCase`/`toUpperCase` normalize for case-insensitive comparison.
- In JavaScript, `padStart`/`padEnd` align fixed-width output like clocks and tables.
- In JavaScript, strings are immutable: every method returns a new string.
- In JavaScript, `String(x)` converts safely while `x.toString()` throws on null/undefined.
