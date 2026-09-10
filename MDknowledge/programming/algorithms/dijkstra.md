# Dijkstra and shortest paths

- Dijkstra finds shortest paths from one source with non-negative weights in O((V+E) log V).
- A min-heap priority queue makes Dijkstra's greedy choice efficient.
- Negative edges break Dijkstra; Bellman-Ford handles them in O(VE).
- Negative cycles make shortest paths undefined; Bellman-Ford detects them.
- Floyd-Warshall computes all-pairs paths in O(V³) for dense small graphs.
- A* adds heuristics to Dijkstra for goal-directed search like game maps.
- Relaxation (dist[v] = min(dist[v], dist[u]+w)) is the core loop of all variants.
- Early exit when the target pops from the heap keeps single-destination queries fast.
- Uniform weights reduce to BFS — skip the heap overhead.
- Road networks precompute contraction hierarchies for millisecond queries.
