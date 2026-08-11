"""
Integration test against a REAL Redis instance (backend/app/cache.py).
Skipped cleanly if Redis isn't reachable at REDIS_URL.
"""

import time

import pytest

from app import cache as redis_cache

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _reset_client_singleton(monkeypatch, redis_up):
    if not redis_up:
        pytest.skip(f"Redis not reachable -- see tests/conftest.py::redis_up")
    # Force a fresh connection attempt against the real REDIS_URL for this test.
    monkeypatch.setattr(redis_cache, "_client", None)


class TestRealRedisRoundtrip:
    def test_set_then_get_roundtrip(self):
        key = redis_cache.geocode_key(f"integration-test-{time.time()}")
        redis_cache.set(key, [13.08, 80.27], ttl=30)
        assert redis_cache.get(key) == [13.08, 80.27]

    def test_missing_key_returns_none(self):
        key = redis_cache.geocode_key(f"does-not-exist-{time.time()}")
        assert redis_cache.get(key) is None

    def test_ttl_expiry(self):
        key = redis_cache.route_key(f"a-{time.time()}", "b", "fastest", "car")
        redis_cache.set(key, {"distance_m": 123}, ttl=1)
        assert redis_cache.get(key) == {"distance_m": 123}
        time.sleep(1.5)
        assert redis_cache.get(key) is None

    def test_stats_reports_connected(self):
        stats = redis_cache.stats()
        assert stats["status"] == "connected"
        assert "cached_keys" in stats
