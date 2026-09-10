# JavaScript JSON

- In JavaScript, `JSON.stringify(value)` serializes; functions, undefined, and symbols are dropped.
- In JavaScript, `JSON.parse(text)` revives plain data and throws `SyntaxError` on malformed input.
- In JavaScript, circular structures throw on stringify; break cycles or use replacer functions.
- In JavaScript, `JSON.stringify(obj, null, 2)` pretty-prints for logs and fixtures.
- In JavaScript, `toJSON()` methods customize per-class serialization output.
- In JavaScript, `Date` stringifies to ISO and parses back as string, not Date — revive manually.
- In JavaScript, `BigInt` throws on stringify; convert to string fields first.
- In JavaScript, reviver functions as the second `JSON.parse` arg transform values during parse.
- In JavaScript, validate parsed JSON shapes before trusting nested fields from the network.
- In JavaScript, `structuredClone` deep-copies better than JSON round-trips for Dates, Maps, and Sets.
