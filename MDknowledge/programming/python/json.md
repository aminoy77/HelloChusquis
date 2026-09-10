# Python json module

- In Python, `json.dumps(obj)` serializes to a string and `json.loads(s)` parses back.
- In Python, `json.dump(obj, f)` writes directly to files and `json.load(f)` reads them.
- In Python, `indent=2` pretty-prints JSON for humans; `sort_keys=True` stabilizes key order.
- In Python, `json.loads` rejects trailing commas and comments, unlike JavaScript or YAML.
- In Python, sets, datetimes, and custom objects need a `default=` function or pre-conversion.
- In Python, `ensure_ascii=False` keeps non-ASCII characters readable instead of escaping them.
- In Python, `json.JSONDecodeError` subclasses ValueError and reports line and column of bad input.
- In Python, `separators=(',', ':')` compacts output for minimal payload sizes.
- In Python, duplicate object keys silently keep the last value when parsing.
- In Python, validate untrusted JSON schemas before acting on nested fields.
