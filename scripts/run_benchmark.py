"""
Produces the real, reproducible numbers quoted in README.md's "Algorithm
Benchmark" and "Redis caching" sections.

Run it yourself:
    .venv/Scripts/python scripts/run_benchmark.py

What it does:
  1. Loads (downloading + on-disk-caching if needed, via the same
     RouteOptimizer/GraphManager code path production uses) a real Chennai
     road network between two real landmarks.
  2. Runs GraphEngine.benchmark() -- the same hand-rolled Dijkstra / A* /
     bidirectional A* / Yen's k-shortest implementations used in production
     -- and reports time_ms / nodes_explored / distance per algorithm.
  3. Calls POST /api/route/calculate twice through the real Flask app (cold
     vs warm) with real Redis to measure the actual cache speed-up.
  4. Writes everything to benchmarks/results_<timestamp>.json.

Nothing here is hand-typed into the README without a corresponding JSON
file in benchmarks/ backing it up.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND_DIR = _REPO_ROOT / "backend"
for _p in (str(_BACKEND_DIR), str(_REPO_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

import osmnx as ox  # noqa: E402

from route_optimizer.config.models import RouteConfig  # noqa: E402
from route_optimizer.intelligence.graph_engine import GraphEngine  # noqa: E402
from route_optimizer.optimizer import RouteOptimizer  # noqa: E402
from route_optimizer.utils.helpers import haversine_distance_m  # noqa: E402

DEFAULT_ORIGIN = "Chennai Central Railway Station, Chennai, India"
DEFAULT_DESTINATION = "T Nagar, Chennai, India"


def load_graph(origin: str, destination: str):
    origin_coords = ox.geocode(origin)
    dest_coords = ox.geocode(destination)

    direct_dist = haversine_distance_m(*origin_coords, *dest_coords)
    radius_m = max(int(direct_dist * 1.5), 3000)
    mid_point = (
        (origin_coords[0] + dest_coords[0]) / 2,
        (origin_coords[1] + dest_coords[1]) / 2,
    )

    config = RouteConfig(graph_cache_dir=str(_REPO_ROOT / "graph_cache"))
    opt = RouteOptimizer(config)
    t0 = time.perf_counter()
    opt.load_graph(center_point=mid_point, radius_m=radius_m)
    load_s = time.perf_counter() - t0

    origin_node = ox.distance.nearest_nodes(opt.graph, origin_coords[1], origin_coords[0])
    dest_node = ox.distance.nearest_nodes(opt.graph, dest_coords[1], dest_coords[0])

    return opt, origin_coords, dest_coords, origin_node, dest_node, load_s


def run_algorithm_benchmark(opt, origin_node, dest_node) -> dict:
    engine = GraphEngine(opt.graph)
    results = engine.benchmark(origin_node, dest_node)

    dijkstra_nodes = results["dijkstra"]["nodes_explored"]
    dijkstra_ms = results["dijkstra"]["time_ms"]

    for algo in ("astar", "bidirectional_astar"):
        nodes = results[algo]["nodes_explored"]
        ms = results[algo]["time_ms"]
        results[algo]["nodes_reduction_x"] = (
            round(dijkstra_nodes / nodes, 2) if nodes else None
        )
        results[algo]["time_reduction_x"] = (
            round(dijkstra_ms / ms, 2) if ms else None
        )

    return results


def run_cache_benchmark(origin: str, destination: str) -> dict:
    import tempfile

    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    from app import cache as redis_cache
    from app import create_app

    app = create_app("benchmark")
    client = app.test_client()

    payload = {
        "origin": origin,
        "destination": destination,
        "route_type": "shortest",
        "vehicle_type": "car",
    }

    # Force a genuine cold run -- an earlier test/benchmark invocation may
    # have already cached this exact origin/destination/route_type/vehicle
    # combination (route cache TTL is 1h). Geocode cache is left alone since
    # that's realistically always warm in production (24h TTL) and isn't
    # what "3,500ms -> 16ms" is measuring.
    rkey = redis_cache.route_key(origin, destination, payload["route_type"], payload["vehicle_type"])
    r = redis_cache._redis()
    if r:
        r.delete(rkey)

    t0 = time.perf_counter()
    cold = client.post("/api/route/calculate", json=payload).get_json()
    cold_ms = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    warm = client.post("/api/route/calculate", json=payload).get_json()
    warm_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "cold_ms": round(cold_ms, 1),
        "warm_ms": round(warm_ms, 1),
        "speedup_x": round(cold_ms / warm_ms, 1) if warm_ms else None,
        "cold_cache_hit": cold.get("cache_hit"),
        "warm_cache_hit": warm.get("cache_hit"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--origin", default=DEFAULT_ORIGIN)
    parser.add_argument("--destination", default=DEFAULT_DESTINATION)
    args = parser.parse_args()

    print(f"Loading graph: {args.origin} -> {args.destination}")
    opt, origin_coords, dest_coords, origin_node, dest_node, load_s = load_graph(
        args.origin, args.destination
    )
    print(f"  graph loaded in {load_s:.1f}s: "
          f"{opt.graph.number_of_nodes()} nodes, {opt.graph.number_of_edges()} edges")

    print("Running algorithm benchmark (Dijkstra / A* / bidirectional A* / Yen's k=3)...")
    algo_results = run_algorithm_benchmark(opt, origin_node, dest_node)
    for name in ("dijkstra", "astar", "bidirectional_astar"):
        r = algo_results[name]
        extra = ""
        if "nodes_reduction_x" in r:
            extra = f"  ({r['nodes_reduction_x']}x fewer nodes, {r['time_reduction_x']}x faster)"
        print(f"  {name:20s} {r['time_ms']:8.3f} ms  {r['nodes_explored']:6d} nodes explored{extra}")
    yen = algo_results["yen_k_shortest"]
    print(f"  {'yen_k_shortest':20s} {yen['time_ms']:8.3f} ms  {yen['paths_found']} paths found")

    print("Running Redis cache benchmark (cold vs warm /api/route/calculate)...")
    cache_results = run_cache_benchmark(args.origin, args.destination)
    print(f"  cold: {cache_results['cold_ms']:.1f} ms (cache_hit={cache_results['cold_cache_hit']})")
    print(f"  warm: {cache_results['warm_ms']:.1f} ms (cache_hit={cache_results['warm_cache_hit']})")
    if cache_results["speedup_x"]:
        print(f"  speedup: {cache_results['speedup_x']}x")

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "origin": {"name": args.origin, "coords": list(origin_coords)},
        "destination": {"name": args.destination, "coords": list(dest_coords)},
        "graph_nodes": opt.graph.number_of_nodes(),
        "graph_edges": opt.graph.number_of_edges(),
        "graph_load_s": round(load_s, 2),
        "algorithm_benchmark": algo_results,
        "cache_benchmark": cache_results,
    }

    out_dir = _REPO_ROOT / "benchmarks"
    out_dir.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_file = out_dir / f"results_{ts}.json"
    out_file.write_text(json.dumps(output, indent=2))
    print(f"\nWrote {out_file.relative_to(_REPO_ROOT)}")


if __name__ == "__main__":
    main()
