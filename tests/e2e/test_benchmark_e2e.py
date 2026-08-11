"""
End-to-end test of POST /api/route/benchmark against a real, live/cached
Chennai-area OSM graph. Asserts the *structural* claims the README makes
about algorithm behaviour (bidirectional A* explores no more nodes than
Dijkstra, all algorithms agree on distance) rather than pinning exact
millisecond/node-count values, which are machine-dependent and would make
this test flaky. The actual numbers quoted in the README come from
scripts/run_benchmark.py's committed output, not from this test.
"""

import pytest

pytestmark = pytest.mark.e2e

_ORIGIN = "Chennai Central Railway Station, Chennai, India"
_DESTINATION = "Chennai International Airport, Chennai, India"


class TestBenchmarkE2E:
    def test_benchmark_structural_invariants(self, client):
        resp = client.post("/api/route/benchmark", json={
            "origin": _ORIGIN,
            "destination": _DESTINATION,
        })
        assert resp.status_code == 200
        data = resp.get_json()

        assert data["success"] is True
        assert data["graph_nodes"] > 1000
        assert data["graph_edges"] > 1000

        r = data["results"]
        dijkstra, astar, bidir = r["dijkstra"], r["astar"], r["bidirectional_astar"]

        # All three must find a path and agree on distance (within 1%).
        for algo in (dijkstra, astar, bidir):
            assert algo["distance"] is not None
        assert astar["distance"] == pytest.approx(dijkstra["distance"], rel=0.01)
        assert bidir["distance"] == pytest.approx(dijkstra["distance"], rel=0.01)

        # The whole architectural claim under test: bidirectional A* explores
        # no more nodes than plain Dijkstra on the same real road graph.
        assert bidir["nodes_explored"] <= dijkstra["nodes_explored"]
        assert astar["nodes_explored"] <= dijkstra["nodes_explored"]

        assert r["yen_k_shortest"]["paths_found"] >= 1
