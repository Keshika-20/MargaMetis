"""
Smoke tests: is the app alive and wired together correctly?
Fast, sqlite-backed, no Redis/network required. These should be the first
thing run in CI -- if these fail, nothing else is worth running.
"""

import pytest

from route_optimizer.intelligence.graph_engine import GraphEngine

pytestmark = pytest.mark.smoke


class TestAppFactory:
    def test_app_creates_successfully(self, flask_app):
        assert flask_app is not None

    def test_all_blueprints_registered(self, flask_app):
        names = {bp for bp in flask_app.blueprints}
        assert names == {"routes", "health", "auth", "admin", "user"}


class TestHealthEndpoints:
    def test_health_check_ok(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"

    def test_cache_stats_ok(self, client):
        resp = client.get("/api/cache/stats")
        assert resp.status_code == 200
        assert "status" in resp.get_json()


class TestGraphEngineTrivialRoute:
    def test_trivial_three_node_route(self, tiny_graph):
        engine = GraphEngine(tiny_graph)
        result = engine.astar(1, 3)
        assert result["path"] == [1, 2, 3]
        assert result["distance"] == pytest.approx(1000.0)
