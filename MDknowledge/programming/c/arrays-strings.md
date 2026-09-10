# C arrays and strings

- In C, `char s[64]` owns 64 mutable bytes while `char *s = "x"` points at read-only storage.
- In C, C strings end with a null terminator, so buffers need `strlen + 1` bytes.
- In C, `strncpy` may skip termination; always set `dst[n-1] = '\0'` explicitly.
- In C, `snprintf(buf, sizeof buf, ...)` formats safely with truncation instead of overflow.
- In C, `strcmp` returns 0 for equality; never compare strings with `==`.
- In C, `strlen` scans for the terminator in O(n); cache it outside loops.
- In C, `memcpy` copies bytes blindly while `memmove` survives overlapping regions.
- In C, `memset(buf, 0, sizeof buf)` zeroes buffers before reuse.
- In C, multidimensional `int m[3][4]` lays out contiguously in row-major order.
- In C, `sizeof(arr)/sizeof(arr[0])` counts elements only where the array is declared.
