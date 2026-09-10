# BFS and DFS

- BFS explores level by level with a queue, finding shortest paths in unweighted graphs.
- DFS dives deep with a stack (or recursion), using less memory on narrow graphs.
- Both run O(V+E) visiting each vertex and edge once with a visited set.
- Forgetting visited sets loops forever on cyclic graphs.
- BFS yields shortest-hop routes for GPS-lite and social degrees.
- DFS detects cycles and produces topological orders via finish times.
- Iterative DFS avoids recursion-depth crashes on deep graphs.
- Bidirectional BFS halves exponent depth meeting search frontiers mid-graph.
- Grid BFS with 4/8-direction moves solves mazes and flood fills.
- Track parents during traversal to reconstruct paths, not just distances.
