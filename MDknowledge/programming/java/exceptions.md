# Java exceptions

- In Java, checked exceptions (`IOException`) must be caught or declared with `throws`.
- In Java, unchecked `RuntimeException`s cover bugs like null dereference and bad arguments.
- In Java, `try-with-resources` closes files, sockets, and streams automatically in order.
- In Java, catch specific types before supertypes or the compiler rejects the order.
- In Java, multi-catch `catch (A | B e)` shares handlers without duplicating bodies.
- In Java, `finally` runs cleanup on every path, including returns and throws.
- In Java, custom exceptions extend `Exception` (checked) or `RuntimeException` (unchecked) by intent.
- In Java, `throw new IllegalArgumentException("msg")` validates public API inputs fast.
- In Java, exception chaining via cause constructors preserves root diagnostics.
- In Java, never swallow with empty catch blocks; at minimum log the stack trace.
