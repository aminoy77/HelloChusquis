# C++ maps

- In C++, `std::map<K,V>` orders keys in a tree with O(log n) access.
- In C++, `std::unordered_map<K,V>` hashes for average O(1) but unordered iteration.
- In C++, `m[k]` inserts default values on miss; `m.at(k)` throws instead.
- In C++, `m.find(k) != m.end()` tests presence without inserting.
- In C++, `m.emplace(k, v)` constructs in place, skipping temporary pairs.
- In C++, iterate with `for (const auto& [k, v] : m)` structured bindings.
- In C++, custom keys need `operator<` for map or a hasher for unordered_map.
- In C++, `m.contains(k)` (C++20) reads clearer than find-compare idioms.
- In C++, erase during iteration via `it = m.erase(it)` to keep iterators valid.
- In C++, `std::set` is the key-only sibling for membership and ordering.
