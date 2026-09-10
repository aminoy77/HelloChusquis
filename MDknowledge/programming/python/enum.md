# Python enum module

- In Python, `class Color(Enum): RED = 1` names constants grouped under one type.
- In Python, `IntEnum` members compare and算术 like ints for flags and codes.
- In Python, `auto()` assigns values automatically to avoid manual numbering drift.
- In Python, `Color(1)` looks up by value and `Color['RED']` looks up by name.
- In Python, iterating an Enum yields members in definition order.
- In Python, `@unique` rejects accidental duplicate values at class creation.
- In Python, `Flag`/`IntFlag` combine members with `|` for permission-style bit sets.
- In Python, `member.name` and `member.value` expose the two sides of each entry.
- In Python, `str(member)` includes the class name; use `.name` for clean labels.
- In Python, JSON-serialize enums via `.value` or a custom encoder, never raw members.
