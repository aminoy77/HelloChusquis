# SQL injection prevention

- SQL injection smuggles queries through concatenated user input.
- Parameterized statements (`?`/`%s` placeholders) separate code from data completely.
- ORMs parameterize by default; raw-string methods reintroduce risk.
- Least-privilege DB users limit blast radius when injection slips through.
- Stored procedures still inject if they concatenate inputs internally.
- Error messages leaking schema details accelerate attacker mapping.
- Allow-list input validation complements, never replaces, parameterization.
- WAF regexes are bypassable cat-and-mouse, not primary defense.
- Second-order injection detonates later from stored payloads — treat stored data as hostile.
- Static analyzers flag string-built SQL in CI before review.
