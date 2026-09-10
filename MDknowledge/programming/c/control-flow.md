# C control flow

- In C, `if/else if/else` chains test conditions top-down with the first match winning.
- In C, `switch` jumps by constant cases; missing `break` falls through to the next case.
- In C, `for (init; cond; step)` loops counted ranges with all three parts optional.
- In C, `while` checks before each iteration and `do-while` guarantees at least one pass.
- In C, `break` exits the innermost loop or switch; `continue` skips to the next iteration.
- In C, `goto` forward-jumps centralize cleanup in C functions lacking exceptions.
- In C, early `return` on error paths flattens nesting better than deep `if` pyramids.
- In C, `?:` ternaries suit tiny value picks, never nested multi-branch logic.
- In C, short-circuit `&&`/`||` guard dereferences: `if (p && p->ok)`.
- In C, infinite servers loop `for (;;)` with explicit break conditions inside.
