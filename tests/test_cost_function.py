"""
Unit tests for A3 — CostFunctionGenerator.
Run with: pytest tests/test_cost_function.py -v
"""

import pytest

from route_optimizer.intelligence.cost_function import (
    CostFunctionGenerator,
    _normalize_weights,
)

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _make_edge(highway: str, length: float = 1000.0, toll: str = "no", maxspeed: str = None) -> dict:
    d = {"highway": highway, "length": length, "toll": toll}
    if maxspeed:
        d["maxspeed"] = maxspeed
    return d


def _constraints(weights: dict, avoid: list = None, prefer: list = None) -> dict:
    dims = ("speed", "safety", "fuel_efficiency", "scenic", "comfort", "cost")
    full = {d: 0.0 for d in dims}
    full.update(weights)
    return {
        "weights": full,
        "avoid": avoid or [],
        "prefer": prefer or [],
    }


# ------------------------------------------------------------------
# Weight normalisation
# ------------------------------------------------------------------

class TestNormalizeWeights:
    def test_already_normalised(self):
        w = {"speed": 0.5, "safety": 0.5}
        result = _normalize_weights(w)
        assert abs(sum(result.values()) - 1.0) < 1e-6

    def test_needs_normalisation(self):
        w = {"speed": 2.0, "safety": 2.0, "comfort": 4.0}
        result = _normalize_weights(w)
        assert abs(sum(result.values()) - 1.0) < 1e-6
        assert abs(result["comfort"] - 0.5) < 1e-6

    def test_zero_total_returns_uniform(self):
        w = {"speed": 0.0, "safety": 0.0}
        result = _normalize_weights(w)
        assert abs(result["speed"] - 0.5) < 1e-6

    def test_single_weight_becomes_one(self):
        w = {"speed": 7.0, "safety": 0.0}
        result = _normalize_weights(w)
        assert abs(result["speed"] - 1.0) < 1e-6


# ------------------------------------------------------------------
# Speed priority: faster roads should be cheaper
# ------------------------------------------------------------------

class TestSpeedPriority:
    def setup_method(self):
        c = _constraints({"speed": 1.0})
        self.fn = CostFunctionGenerator(c).generate()

    def test_motorway_cheaper_than_residential_same_length(self):
        motorway = _make_edge("motorway", 1000)
        residential = _make_edge("residential", 1000)
        assert self.fn(1, 2, motorway) < self.fn(1, 2, residential)

    def test_primary_cheaper_than_tertiary(self):
        primary = _make_edge("primary", 500)
        tertiary = _make_edge("tertiary", 500)
        assert self.fn(1, 2, primary) < self.fn(1, 2, tertiary)

    def test_longer_same_type_is_more_expensive(self):
        short = _make_edge("primary", 500)
        long_ = _make_edge("primary", 1000)
        assert self.fn(1, 2, short) < self.fn(1, 2, long_)

    def test_maxspeed_tag_affects_cost(self):
        fast = _make_edge("primary", 1000, maxspeed="100")
        slow = _make_edge("primary", 1000, maxspeed="20")
        assert self.fn(1, 2, fast) < self.fn(1, 2, slow)


# ------------------------------------------------------------------
# Scenic priority: quiet roads should be cheaper
# ------------------------------------------------------------------

class TestScenicPriority:
    def setup_method(self):
        c = _constraints({"scenic": 1.0})
        self.fn = CostFunctionGenerator(c).generate()

    def test_residential_cheaper_than_motorway(self):
        residential = _make_edge("residential", 1000)
        motorway = _make_edge("motorway", 1000)
        assert self.fn(1, 2, residential) < self.fn(1, 2, motorway)

    def test_unclassified_cheaper_than_primary(self):
        unclassified = _make_edge("unclassified", 1000)
        primary = _make_edge("primary", 1000)
        assert self.fn(1, 2, unclassified) < self.fn(1, 2, primary)

    def test_motorway_is_most_scenic_expensive(self):
        motorway = _make_edge("motorway", 1000)
        tertiary = _make_edge("tertiary", 1000)
        assert self.fn(1, 2, motorway) > self.fn(1, 2, tertiary)


# ------------------------------------------------------------------
# Safety priority: safer roads should be cheaper
# ------------------------------------------------------------------

class TestSafetyPriority:
    def setup_method(self):
        c = _constraints({"safety": 1.0})
        self.fn = CostFunctionGenerator(c).generate()

    def test_motorway_safer_than_track(self):
        motorway = _make_edge("motorway", 1000)
        track = _make_edge("track", 1000)
        assert self.fn(1, 2, motorway) < self.fn(1, 2, track)

    def test_primary_safer_than_service(self):
        primary = _make_edge("primary", 1000)
        service = _make_edge("service", 1000)
        assert self.fn(1, 2, primary) < self.fn(1, 2, service)


# ------------------------------------------------------------------
# Avoid tolls: toll roads must be heavily penalised
# ------------------------------------------------------------------

class TestAvoidTolls:
    def setup_method(self):
        c = _constraints({"cost": 1.0}, avoid=["tolls"])
        self.fn = CostFunctionGenerator(c).generate()

    def test_toll_road_far_more_expensive(self):
        toll = _make_edge("motorway", 1000, toll="yes")
        free = _make_edge("motorway", 1000, toll="no")
        assert self.fn(1, 2, toll) > self.fn(1, 2, free) * 50

    def test_very_long_free_road_still_cheaper_than_short_toll(self):
        toll_short = _make_edge("motorway", 100, toll="yes")
        free_long = _make_edge("motorway", 2000, toll="no")
        assert self.fn(1, 2, free_long) < self.fn(1, 2, toll_short)


# ------------------------------------------------------------------
# Avoid highways
# ------------------------------------------------------------------

class TestAvoidHighways:
    def setup_method(self):
        c = _constraints({"speed": 1.0}, avoid=["highways"])
        self.fn = CostFunctionGenerator(c).generate()

    def test_motorway_penalised(self):
        motorway = _make_edge("motorway", 1000)
        secondary = _make_edge("secondary", 1000)
        assert self.fn(1, 2, motorway) > self.fn(1, 2, secondary)

    def test_trunk_penalised(self):
        trunk = _make_edge("trunk", 1000)
        tertiary = _make_edge("tertiary", 1000)
        assert self.fn(1, 2, trunk) > self.fn(1, 2, tertiary)


# ------------------------------------------------------------------
# Prefer highways: should discount cost
# ------------------------------------------------------------------

class TestPreferHighways:
    def test_prefer_highways_discounts_motorway(self):
        c_prefer = _constraints({"speed": 1.0}, prefer=["highways"])
        c_neutral = _constraints({"speed": 1.0})
        fn_prefer = CostFunctionGenerator(c_prefer).generate()
        fn_neutral = CostFunctionGenerator(c_neutral).generate()
        motorway = _make_edge("motorway", 1000)
        assert fn_prefer(1, 2, motorway) < fn_neutral(1, 2, motorway)


# ------------------------------------------------------------------
# Highway type as list (OSMnx sometimes returns list)
# ------------------------------------------------------------------

class TestHighwayList:
    def test_list_highway_does_not_crash(self):
        c = _constraints({"speed": 1.0})
        fn = CostFunctionGenerator(c).generate()
        edge_with_list = {"highway": ["primary", "secondary"], "length": 500.0}
        cost = fn(1, 2, edge_with_list)
        assert cost > 0

    def test_unknown_highway_falls_back_gracefully(self):
        c = _constraints({"speed": 1.0})
        fn = CostFunctionGenerator(c).generate()
        unknown = {"highway": "aeroway", "length": 800.0}
        cost = fn(1, 2, unknown)
        assert cost > 0 and cost != float("inf")


# ------------------------------------------------------------------
# Cost function describe()
# ------------------------------------------------------------------

class TestDescribe:
    def test_describe_non_empty(self):
        c = _constraints({"speed": 0.6, "safety": 0.4})
        gen = CostFunctionGenerator(c)
        desc = gen.describe()
        assert "speed" in desc or "safety" in desc

    def test_describe_only_shows_nonzero(self):
        c = _constraints({"speed": 1.0})
        gen = CostFunctionGenerator(c)
        desc = gen.describe()
        # scenic weight is 0 — should not appear
        assert "scenic=0.00" not in desc


# ------------------------------------------------------------------
# Mixed weight correctness
# ------------------------------------------------------------------

class TestMixedWeights:
    def test_weights_sum_to_one_after_normalisation(self):
        raw = {"speed": 3.0, "safety": 1.0, "scenic": 2.0}
        c = _constraints(raw)
        gen = CostFunctionGenerator(c)
        total = sum(gen.weights.values())
        assert abs(total - 1.0) < 1e-4

    def test_zero_length_edge_returns_small_cost(self):
        c = _constraints({"speed": 1.0})
        fn = CostFunctionGenerator(c).generate()
        zero_edge = {"highway": "primary", "length": 0.0}
        cost = fn(1, 2, zero_edge)
        assert cost >= 0
