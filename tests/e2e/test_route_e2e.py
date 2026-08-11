"""
Backend-only end-to-end tests: real Flask app + real Redis (if reachable) +
real OSM data (live geocoding + live/cached graph download via GraphManager,
exactly the production code path -- nothing mocked).

Slow and network-dependent by design -- run with `pytest -m e2e`.
First run downloads a real Chennai-area road graph (~tens of MB, ~20-40s);
subsequent runs hit the on-disk graph_cache/ and are fast.
"""

import pytest

pytestmark = pytest.mark.e2e

_ORIGIN = "Chennai Central Railway Station, Chennai, India"
_DESTINATION = "Chennai International Airport, Chennai, India"


class TestRouteCalculateE2E:
    def test_real_route_between_chennai_landmarks(self, client):
        resp = client.post("/api/route/calculate", json={
            "origin": _ORIGIN,
            "destination": _DESTINATION,
            "route_type": "shortest",
            "vehicle_type": "car",
        })
        assert resp.status_code == 200
        data = resp.get_json()

        assert data["success"] is True
        # Real Chennai Central -> Airport is a genuine multi-km drive.
        assert 8_000 < data["distance_m"] < 40_000
        assert data["path_nodes"] > 10
        assert data["estimated_time_min"] > 0
        assert data["confidence"] is not None
        assert data["confidence"]["risk_level"] in ("Low", "Medium", "High")


class TestSmartRouteE2E:
    def test_real_smart_route_avoiding_tolls(self, client):
        resp = client.post("/api/route/smart", json={
            "query": "fastest route avoiding tolls",
            "origin": _ORIGIN,
            "destination": _DESTINATION,
        })
        assert resp.status_code == 200
        data = resp.get_json()

        assert data["success"] is True
        assert len(data["routes"]) >= 1
        assert "tolls" in data["constraints"]["avoid"]
        best = data["routes"][0]
        assert best["distance_m"] > 0
        assert best["eta_min"] > 0
