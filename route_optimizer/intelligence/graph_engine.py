"""
A1 — Graph Engine
Implements Dijkstra, A* (Haversine heuristic), Bidirectional A*, and
Yen's K-Shortest Paths from scratch.  Dynamic edge reweighting via an
injected cost callable.  Benchmark() runs all four and records ms.
"""

import heapq
import math
import time
from typing import Callable, Dict, List, Optional, Tuple

import networkx as nx


class GraphEngine:
    """
    All pathfinding is hand-rolled — no nx.astar_path or similar.
    weight_fn signature: (u: int, v: int, edge_data: dict) -> float
    When weight_fn is None, edge 'length' (metres) is used.
    """

    def __init__(self, graph: nx.MultiDiGraph) -> None:
        self.graph = graph
        self._coord_cache: Dict[int, Tuple[float, float]] = {}

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _coords(self, node: int) -> Tuple[float, float]:
        if node not in self._coord_cache:
            d = self.graph.nodes[node]
            self._coord_cache[node] = (float(d["y"]), float(d["x"]))
        return self._coord_cache[node]

    def _haversine(self, a: int, b: int) -> float:
        lat1, lon1 = self._coords(a)
        lat2, lon2 = self._coords(b)
        R = 6_371_000.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        h = math.sin(dlat / 2) ** 2 + (
            math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2) ** 2
        )
        return R * 2.0 * math.asin(math.sqrt(max(0.0, h)))

    def _edge_weight(
        self, u: int, v: int, weight_fn: Optional[Callable] = None
    ) -> float:
        """Minimum cost across all parallel edges (MultiDiGraph)."""
        edge_dict = self.graph.get_edge_data(u, v)
        if not edge_dict:
            return float("inf")
        if weight_fn is not None:
            return min(weight_fn(u, v, data) for data in edge_dict.values())
        return min(data.get("length", float("inf")) for data in edge_dict.values())

    def _path_cost(
        self, path: List[int], weight_fn: Optional[Callable] = None
    ) -> float:
        return sum(
            self._edge_weight(path[i], path[i + 1], weight_fn)
            for i in range(len(path) - 1)
        )

    @staticmethod
    def _reconstruct(came_from: Dict, start: int, end: int) -> List[int]:
        path: List[int] = []
        cur: int = end
        while cur != start:
            path.append(cur)
            cur = came_from[cur]
        path.append(start)
        path.reverse()
        return path

    # ------------------------------------------------------------------ #
    # Algorithm 1 — Dijkstra                                              #
    # ------------------------------------------------------------------ #

    def dijkstra(
        self,
        origin: int,
        destination: int,
        weight_fn: Optional[Callable] = None,
    ) -> Dict:
        t0 = time.perf_counter()
        dist: Dict[int, float] = {origin: 0.0}
        came_from: Dict[int, int] = {}
        heap = [(0.0, origin)]
        closed: set = set()
        nodes_explored = 0

        while heap:
            d, u = heapq.heappop(heap)
            if u in closed:
                continue
            closed.add(u)
            nodes_explored += 1
            if u == destination:
                break
            for v in self.graph.successors(u):
                w = self._edge_weight(u, v, weight_fn)
                nd = d + w
                if nd < dist.get(v, float("inf")):
                    dist[v] = nd
                    came_from[v] = u
                    heapq.heappush(heap, (nd, v))

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if destination not in dist:
            return {
                "path": None,
                "distance": float("inf"),
                "time_ms": elapsed_ms,
                "nodes_explored": nodes_explored,
            }
        return {
            "path": self._reconstruct(came_from, origin, destination),
            "distance": dist[destination],
            "time_ms": elapsed_ms,
            "nodes_explored": nodes_explored,
        }

    # ------------------------------------------------------------------ #
    # Algorithm 2 — A* with Haversine heuristic                          #
    # ------------------------------------------------------------------ #

    def astar(
        self,
        origin: int,
        destination: int,
        weight_fn: Optional[Callable] = None,
    ) -> Dict:
        t0 = time.perf_counter()
        g: Dict[int, float] = {origin: 0.0}
        came_from: Dict[int, int] = {}
        # heap tuple: (f_score, g_score, node)
        heap = [(self._haversine(origin, destination), 0.0, origin)]
        closed: set = set()
        nodes_explored = 0

        while heap:
            _, g_val, u = heapq.heappop(heap)
            if u in closed:
                continue
            closed.add(u)
            nodes_explored += 1
            if u == destination:
                break
            for v in self.graph.successors(u):
                w = self._edge_weight(u, v, weight_fn)
                ng = g[u] + w
                if ng < g.get(v, float("inf")):
                    g[v] = ng
                    came_from[v] = u
                    f = ng + self._haversine(v, destination)
                    heapq.heappush(heap, (f, ng, v))

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if destination not in g:
            return {
                "path": None,
                "distance": float("inf"),
                "time_ms": elapsed_ms,
                "nodes_explored": nodes_explored,
            }
        return {
            "path": self._reconstruct(came_from, origin, destination),
            "distance": g[destination],
            "time_ms": elapsed_ms,
            "nodes_explored": nodes_explored,
        }

    # ------------------------------------------------------------------ #
    # Algorithm 3 — Bidirectional A*                                      #
    # ------------------------------------------------------------------ #

    def bidirectional_astar(
        self,
        origin: int,
        destination: int,
        weight_fn: Optional[Callable] = None,
    ) -> Dict:
        if origin == destination:
            return {
                "path": [origin],
                "distance": 0.0,
                "time_ms": 0.0,
                "nodes_explored": 0,
            }

        t0 = time.perf_counter()

        # Forward from origin
        g_fwd: Dict[int, float] = {origin: 0.0}
        prev_fwd: Dict[int, Optional[int]] = {origin: None}
        heap_fwd = [(self._haversine(origin, destination), 0.0, origin)]
        closed_fwd: Dict[int, float] = {}

        # Backward from destination (traverses reversed edges)
        g_bwd: Dict[int, float] = {destination: 0.0}
        prev_bwd: Dict[int, Optional[int]] = {destination: None}
        heap_bwd = [(self._haversine(destination, origin), 0.0, destination)]
        closed_bwd: Dict[int, float] = {}

        best = float("inf")
        meeting: Optional[int] = None
        nodes_explored = 0

        while heap_fwd or heap_bwd:
            # ---- forward step ----
            if heap_fwd:
                _, g_val, u = heapq.heappop(heap_fwd)
                if u not in closed_fwd:
                    closed_fwd[u] = g_fwd[u]
                    nodes_explored += 1
                    if u in closed_bwd:
                        c = g_fwd[u] + g_bwd[u]
                        if c < best:
                            best, meeting = c, u
                    for v in self.graph.successors(u):
                        w = self._edge_weight(u, v, weight_fn)
                        ng = g_fwd[u] + w
                        if ng < g_fwd.get(v, float("inf")):
                            g_fwd[v] = ng
                            prev_fwd[v] = u
                            heapq.heappush(
                                heap_fwd,
                                (ng + self._haversine(v, destination), ng, v),
                            )
                        if v in closed_bwd:
                            c = ng + g_bwd[v]
                            if c < best:
                                best, meeting = c, v

            # ---- backward step ----
            if heap_bwd:
                _, g_val, u = heapq.heappop(heap_bwd)
                if u not in closed_bwd:
                    closed_bwd[u] = g_bwd[u]
                    nodes_explored += 1
                    if u in closed_fwd:
                        c = g_fwd[u] + g_bwd[u]
                        if c < best:
                            best, meeting = c, u
                    for v in self.graph.predecessors(u):
                        w = self._edge_weight(v, u, weight_fn)
                        ng = g_bwd[u] + w
                        if ng < g_bwd.get(v, float("inf")):
                            g_bwd[v] = ng
                            prev_bwd[v] = u
                            heapq.heappush(
                                heap_bwd,
                                (ng + self._haversine(v, origin), ng, v),
                            )
                        if v in closed_fwd:
                            c = g_fwd[v] + ng
                            if c < best:
                                best, meeting = c, v

            # Termination: sum of next-best g-scores from both frontiers >= best
            g_top_fwd = heap_fwd[0][1] if heap_fwd else float("inf")
            g_top_bwd = heap_bwd[0][1] if heap_bwd else float("inf")
            if g_top_fwd + g_top_bwd >= best:
                break

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if meeting is None:
            return {
                "path": None,
                "distance": float("inf"),
                "time_ms": elapsed_ms,
                "nodes_explored": nodes_explored,
            }

        # Reconstruct origin → meeting
        fwd_path: List[int] = []
        cur: Optional[int] = meeting
        while cur is not None:
            fwd_path.append(cur)
            cur = prev_fwd.get(cur)
        fwd_path.reverse()

        # Reconstruct meeting → destination (skip meeting node)
        bwd_path: List[int] = []
        cur = prev_bwd.get(meeting)
        while cur is not None:
            bwd_path.append(cur)
            cur = prev_bwd.get(cur)

        return {
            "path": fwd_path + bwd_path,
            "distance": best,
            "time_ms": elapsed_ms,
            "nodes_explored": nodes_explored,
        }

    # ------------------------------------------------------------------ #
    # Algorithm 4 — Yen's K-Shortest Paths                               #
    # ------------------------------------------------------------------ #

    def yen_k_shortest(
        self,
        origin: int,
        destination: int,
        k: int = 3,
        weight_fn: Optional[Callable] = None,
    ) -> List[Dict]:
        """
        Yen's K-Shortest Paths — optimised with edge/node blocking instead of
        graph copies.  Avoids O(N) graph.copy() on every spur, reducing
        runtime from O(k·|path|·N) to O(k·|path|·|E|·log|N|).
        """
        t0 = time.perf_counter()

        first = self.astar(origin, destination, weight_fn)
        if first["path"] is None:
            return []

        A: List[Dict] = [{"path": first["path"], "distance": first["distance"]}]
        B: List[Dict] = []  # candidate pool

        for ki in range(1, k):
            prev_path = A[ki - 1]["path"]

            for i in range(len(prev_path) - 1):
                spur_node = prev_path[i]
                root_path = prev_path[: i + 1]
                root_cost = self._path_cost(root_path, weight_fn)

                # Build blocked sets — O(k·i), no graph copy
                blocked_edges: set = set()
                blocked_nodes: set = set(root_path[:-1])  # exclude spur_node

                for path_info in A:
                    p = path_info["path"]
                    if len(p) > i and p[: i + 1] == root_path:
                        blocked_edges.add((p[i], p[i + 1]))

                spur_result = self._astar_blocked(
                    spur_node, destination, weight_fn, blocked_edges, blocked_nodes
                )

                if spur_result["path"] is not None:
                    total_path = root_path[:-1] + spur_result["path"]
                    total_cost = root_cost + spur_result["distance"]
                    candidate = {"path": total_path, "distance": total_cost}
                    if not any(c["path"] == total_path for c in B):
                        B.append(candidate)

            if not B:
                break

            B.sort(key=lambda x: x["distance"])
            A.append(B.pop(0))

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        for route in A:
            route["time_ms"] = elapsed_ms

        return A

    def _astar_blocked(
        self,
        origin: int,
        destination: int,
        weight_fn: Optional[Callable],
        blocked_edges: set,
        blocked_nodes: set,
    ) -> Dict:
        """A* that skips blocked edges and blocked nodes (used by Yen's)."""
        t0 = time.perf_counter()
        g: Dict[int, float] = {origin: 0.0}
        came_from: Dict[int, int] = {}
        heap = [(self._haversine(origin, destination), 0.0, origin)]
        closed: set = set()
        nodes_explored = 0

        while heap:
            _, g_val, u = heapq.heappop(heap)
            if u in closed or u in blocked_nodes:
                continue
            closed.add(u)
            nodes_explored += 1
            if u == destination:
                break
            for v in self.graph.successors(u):
                if v in blocked_nodes or (u, v) in blocked_edges:
                    continue
                w = self._edge_weight(u, v, weight_fn)
                ng = g[u] + w
                if ng < g.get(v, float("inf")):
                    g[v] = ng
                    came_from[v] = u
                    heapq.heappush(heap, (ng + self._haversine(v, destination), ng, v))

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if destination not in g:
            return {"path": None, "distance": float("inf"),
                    "time_ms": elapsed_ms, "nodes_explored": nodes_explored}
        return {"path": self._reconstruct(came_from, origin, destination),
                "distance": g[destination], "time_ms": elapsed_ms,
                "nodes_explored": nodes_explored}

    # ------------------------------------------------------------------ #
    # Benchmark                                                           #
    # ------------------------------------------------------------------ #

    def benchmark(
        self,
        origin: int,
        destination: int,
        weight_fn: Optional[Callable] = None,
    ) -> Dict:
        """
        Run all four algorithms on the same (origin, destination) pair.
        Returns a dict keyed by algorithm name with time_ms, distance,
        nodes_explored, path_length — ready for resume / interview demos.
        """
        results: Dict = {}

        for name, fn in [
            ("dijkstra", self.dijkstra),
            ("astar", self.astar),
            ("bidirectional_astar", self.bidirectional_astar),
        ]:
            r = fn(origin, destination, weight_fn)
            results[name] = {
                "time_ms": round(r["time_ms"], 3),
                "distance": round(r["distance"], 2) if r["distance"] != float("inf") else None,
                "nodes_explored": r.get("nodes_explored", 0),
                "path_length": len(r["path"]) if r["path"] else 0,
            }

        k_routes = self.yen_k_shortest(origin, destination, k=3, weight_fn=weight_fn)
        results["yen_k_shortest"] = {
            "time_ms": round(k_routes[0]["time_ms"], 3) if k_routes else 0.0,
            "paths_found": len(k_routes),
            "distances": [round(r["distance"], 2) for r in k_routes],
        }

        return results

    # ------------------------------------------------------------------ #
    # Dynamic edge reweighting                                            #
    # ------------------------------------------------------------------ #

    def reweight_edges(self, cost_fn: Callable) -> None:
        """
        Bake a cost function into every edge as '_dyn_weight'.
        Alternative to passing cost_fn at query time — useful when you
        want to pre-compute weights once for repeated queries.
        """
        for u, v, key, data in self.graph.edges(keys=True, data=True):
            data["_dyn_weight"] = cost_fn(u, v, data)
