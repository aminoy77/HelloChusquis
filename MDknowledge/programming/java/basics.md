# Java basics

- In Java, each public class lives in its own `Name.java` file and the program starts at `public static void main(String[] args)`.
- In Java, `javac Main.java` compiles and `java Main` runs; build tools like Maven or Gradle manage real projects.
- In Java, primitive types (`int`, `double`, `boolean`, `char`) hold values directly while objects are accessed by reference.
- In Java, `String` is immutable: concatenation creates new objects, so build in loops with `StringBuilder`.
- In Java, compare strings with `.equals()`, never `==`, which tests reference identity.
- In Java, `ArrayList<String> list = new ArrayList<>();` gives a resizable array with `add`, `get`, `set`, and `size()`.
- In Java, arrays have fixed length (`new int[10]`) and expose it as the `length` field, not a method.
- In Java, `HashMap<String, Integer>` maps keys to values with `put`, `get`, `getOrDefault`, and `containsKey`.
- In Java, `for (String s : list)` enhanced loops read cleanly; use indexed loops only when the position matters.
- In Java, checked exceptions must be caught or declared with `throws`; unchecked (`RuntimeException`) need neither.
- In Java, `try-with-resources` (`try (var r = open())`) closes files, sockets, and streams automatically.
- In Java, `==` on primitives compares values; on objects it compares identity — use `.equals()` for content.
- In Java, `static` members belong to the class, not instances; `main` being static is why it cannot use instance fields directly.
- In Java, `final` on variables forbids reassignment, on methods forbids overriding, and on classes forbids subclassing.
- In Java, interfaces declare contracts (`implements`) and abstract classes share partial implementations (`extends`).
- In Java, `@Override` catches signature mismatches at compile time when intending to override.
- In Java, generics like `List<String>` are erased at runtime; every element still needs its declared type at compile time.
- In Java, `Optional<T>` expresses possibly-absent returns better than returning null into the codebase.
