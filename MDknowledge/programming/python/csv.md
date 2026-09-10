# Python csv module

- In Python, open CSV files with `newline=''` so the csv module controls line endings.
- In Python, `csv.reader(f)` yields rows as lists and `csv.DictReader(f)` as dicts.
- In Python, `csv.writer(f)` and `csv.DictWriter(f, fieldnames=[...])` emit rows safely quoted.
- In Python, `DictWriter.writeheader()` writes the header row from fieldnames once.
- In Python, `delimiter=';'` and `quotechar` adapt to European and legacy dialects.
- In Python, `csv.Sniffer().sniff(sample)` detects unknown delimiters heuristically.
- In Python, always pass `encoding='utf-8-sig'` when Excel compatibility matters.
- In Python, `quoting=csv.QUOTE_MINIMAL` is the sane default for most outputs.
- In Python, stream row-by-row instead of `list(reader)` for multi-gigabyte files.
- In Python, malformed rows raise `csv.Error`; validate counts per row defensively.
