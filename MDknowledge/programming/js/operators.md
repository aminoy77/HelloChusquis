# JavaScript operators

- In JavaScript, `===` compares without coercion; `==` coerces and causes classic bugs — prefer `===`.
- In JavaScript, `??` defaults only on null/undefined while `||` also triggers on 0, '', and false.
- In JavaScript, `?.` short-circuits nullish chains instead of throwing TypeError.
- In JavaScript, `...` spreads iterables into calls/arrays and collects rest params in functions.
- In JavaScript, `&&` and `||` return operand values, not booleans — handy but surprising in JSX/strings.
- In JavaScript, `++`/`--` mutate and return pre/post values; prefer `+= 1` for clarity.
- In JavaScript, `%` keeps the dividend's sign for negatives (`-5 % 2 === -1`).
- In JavaScript, `**` exponentiates and `**=` assigns; it binds tighter than unary minus.
- In JavaScript, `in` checks keys, `instanceof` checks prototype chains, `typeof` names primitives.
- In JavaScript, comma expressions evaluate left-to-right returning the last value — avoid outside `for` headers.
