# Java collections

- In Java, `ArrayList` gives indexed dynamic arrays while `LinkedList` favors deque ends.
- In Java, `HashMap` offers average O(1) lookup with unordered iteration.
- In Java, `TreeMap`/`TreeSet` sort keys via natural order or a `Comparator`.
- In Java, `HashSet` dedupes with `add` returning false for existing elements.
- In Java, `ArrayDeque` implements both stacks and queues more efficiently than legacy `Stack`.
- In Java, `Collections.unmodifiableList` views and `List.of` factories share read-only data safely.
- In Java, `Map.of` builds small immutable maps inline for configs and tests.
- In Java, iterate with enhanced for-loops; remove via `Iterator.remove` to avoid `ConcurrentModificationException`.
- In Java, `computeIfAbsent` lazily initializes map values without double lookup.
- In Java, `Collections.sort` plus custom `Comparator.comparing` orders domain objects declaratively.
