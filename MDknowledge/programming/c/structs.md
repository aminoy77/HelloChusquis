# C structs

- In C, `struct Point { int x; int y; };` defines a record type grouping related fields.
- In C, `typedef struct { ... } Point;` lets you write `Point p;` without repeating `struct`.
- In C, access fields with `p.x` for values and `ptr->x` for pointers to structs.
- In C, initialize with `struct Point p = {.x = 1, .y = 2};` using designated initializers.
- In C, `sizeof(struct S)` may exceed the sum of fields because of alignment padding between members.
- In C, order struct fields from largest to smallest alignment to minimize padding waste.
- In C, never compare structs with `==`; compare field by field or with `memcmp` only for padding-free layouts.
- In C, `struct` assignment (`a = b;`) copies member-wise, duplicating any embedded arrays.
- In C, `union` overlays members in shared storage; only the last-written member holds a valid value.
- In C, `enum Color { RED, GREEN, BLUE };` names integer constants starting at 0 unless assigned.
- In C, pass large structs by pointer (`const struct S *`) to avoid expensive copies.
- In C, opaque pointers (`typedef struct Handle Handle;` with hidden definition) encapsulate library internals.
- In C, bit-fields (`unsigned flag : 1;`) pack small integers but their layout is implementation-defined.
- In C, `offsetof(struct S, field)` from `<stddef.h>` gives a field's byte offset portably.
- In C, flexible array members plus one oversized `malloc` implement variable-length records efficiently.
- In C, forward-declare `struct Node;` to build self-referential types like linked lists.
- In C, `static` functions and file-scope variables hide module internals from other translation units.
- In C, header files carry declarations while exactly one `.c` file provides each definition.
