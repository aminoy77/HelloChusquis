# Python random module

- In Python, `random.random()` returns floats in [0.0, 1.0) and `randint(a, b)` includes both ends.
- In Python, `random.choice(seq)` picks one element and `random.sample(seq, k)` picks k unique ones.
- In Python, `random.shuffle(list)` shuffles in place and returns None.
- In Python, `random.seed(n)` reproduces sequences for tests; unseeded runs differ each time.
- In Python, the `random` module is deterministic and unsuitable for secrets; use `secrets` instead.
- In Python, `random.uniform(a, b)` draws floats and `random.gauss(mu, sigma)` draws normally distributed ones.
- In Python, `random.choices(seq, weights=[...], k=n)` samples with replacement by weight.
- In Python, `random.randrange(start, stop, step)` mirrors `range` semantics for random picks.
- In Python, `secrets.token_hex(n)` and `secrets.token_urlsafe(n)` generate secure tokens.
- In Python, `secrets.choice` picks securely from sequences for passwords and salts.
