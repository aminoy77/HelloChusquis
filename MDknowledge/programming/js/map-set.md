# JavaScript Map and Set

- In JavaScript, `new Map()` keys by identity, accepting objects where plain objects coerce to strings.
- In JavaScript, `map.set/get/has/delete` plus `map.size` cover the whole Map API.
- In JavaScript, `new Set(values)` dedupes; `set.has(x)` membership is sublinear.
- In JavaScript, `[...new Set(arr)]` is the idiomatic primitive dedupe one-liner.
- In JavaScript, `WeakMap`/`WeakSet` hold keys weakly, letting garbage collection reclaim entries.
- In JavaScript, iterate Maps with `for (const [k, v] of map)` preserving insertion order.
- In JavaScript, `Object.fromEntries(map)` converts back to plain objects for JSON.
- In JavaScript, prefer Map for dynamic key sets and plain objects for fixed-shape records.
- In JavaScript, `map.forEach((v, k) => ...)` passes value first, unlike array forEach.
- In JavaScript, serialize Maps explicitly; `JSON.stringify(new Map())` yields `{}`.
