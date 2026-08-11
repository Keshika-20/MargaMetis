"""Unit tests for route_optimizer/utils/helpers.py."""

import pytest

from route_optimizer.utils.helpers import estimate_travel_time, haversine_distance_m

pytestmark = pytest.mark.unit


class TestHaversineDistance:
    def test_zero_distance_for_identical_points(self):
        assert haversine_distance_m(13.0827, 80.2707, 13.0827, 80.2707) == pytest.approx(0.0, abs=1e-6)

    def test_known_real_world_distance(self):
        # Chennai Central (13.0827, 80.2707) to Chennai Airport (12.9941, 80.1709)
        # straight-line distance is ~13.5 km.
        dist_m = haversine_distance_m(13.0827, 80.2707, 12.9941, 80.1709)
        assert 12_000 < dist_m < 15_000

    def test_symmetric(self):
        a = haversine_distance_m(13.0827, 80.2707, 12.9941, 80.1709)
        b = haversine_distance_m(12.9941, 80.1709, 13.0827, 80.2707)
        assert a == pytest.approx(b, rel=1e-9)


class TestEstimateTravelTime:
    def test_returns_all_modes(self):
        times = estimate_travel_time(10_000)
        assert set(times.keys()) == {"Car", "Bike", "Walk"}

    def test_walk_slower_than_bike_slower_than_car(self):
        times = estimate_travel_time(10_000)
        assert times["Car"] < times["Bike"] < times["Walk"]

    def test_zero_distance_zero_time(self):
        times = estimate_travel_time(0)
        assert all(t == 0 for t in times.values())
