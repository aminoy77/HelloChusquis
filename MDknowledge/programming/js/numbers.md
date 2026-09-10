# JavaScript numbers

- In JavaScript, all numbers are IEEE-754 doubles; `0.1 + 0.2` equals `0.30000000000000004`.
- In JavaScript, compare floats with an epsilon (`Math.abs(a-b) < 1e-9`) instead of `===`.
- In JavaScript, `Number.isNaN` checks real NaN without coercing; the global `isNaN` coerces first.
- In JavaScript, `Number.isInteger` and `Number.isFinite` validate before arithmetic.
- In JavaScript, `Math.floor/ceil/round/trunc` cover the four rounding directions.
- In JavaScript, `toFixed(2)` formats currency strings; it returns a string, not a number.
- In JavaScript, `parseInt('08')` needs a radix (`parseInt(s, 10)`) to avoid octal surprises.
- In JavaScript, `BigInt` (`10n`) handles integers beyond `Number.MAX_SAFE_INTEGER` exactly.
- In JavaScript, `Math.max(...arr)` spreads arrays into variadic math functions.
- In JavaScript, `Math.random()` yields [0,1); scale and floor it for integer ranges.
