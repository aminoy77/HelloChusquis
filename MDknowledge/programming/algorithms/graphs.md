# Graphs

- Graphs model entities plus relationships: social nets, roads, dependencies.
- Adjacency lists suit sparse graphs; matrices suit dense ones with O(1) edge tests.
- Directed edges model one-way flows (web links); undirected model mutual ties.
- Topological sort orders DAG tasks so dependencies precede dependents.
- Cycles in dependency graphs deadlock builds; detect via DFS coloring.
- Connected components label isolated subgraphs in one linear pass.
- Minimum spanning trees (Kruskal, Prim) wire all nodes cheapest.
- PageRank ranks nodes by link structure iteratively to convergence.
- Bipartite checks (two-coloring) validate matching and scheduling problems.
- Eulerian trails use every edge once; Hamiltonian paths visit every vertex once (NP-complete).
