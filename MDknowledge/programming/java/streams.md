# Java streams

- In Java, `list.stream()` pipelines `filter`, `map`, and `collect` without mutating sources.
- In Java, intermediate ops are lazy; nothing runs until a terminal op like `collect` or `forEach`.
- In Java, `Collectors.toList()` gathers results; `toMap` and `groupingBy` reshape them.
- In Java, `mapToInt(...).sum()` avoids boxing overhead for numeric reductions.
- In Java, `findFirst` returns `Optional`; handle emptiness instead of calling `get` blindly.
- In Java, `anyMatch`/`allMatch` short-circuit predicates like loop breaks.
- In Java, `distinct()` dedupes via `equals` and `sorted()` orders with comparators.
- In Java, `flatMap` flattens nested streams from one-to-many mappings.
- In Java, `parallelStream()` speeds CPU-bound bulk work but scrambles encounter order.
- In Java, streams are single-use; reuse triggers `IllegalStateException`.
