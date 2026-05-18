"""
A3 — Dynamic Cost Function Generator
Takes a constraint JSON dict and returns a Python callable at runtime.
The callable is injected directly into graph traversal — not a config file.

cost_fn(u, v, edge_data) -> float
"""

from typing import Any, Callable, Dict, List

# ------------------------------------------------------------------ #
# Road-type lookup tables                                             #
# ------------------------------------------------------------------ #

_SPEED_KMPH: Dict[str, float] = {
    "motorway": 100.0,
    "motorway_link": 80.0,
    "trunk": 80.0,
    "trunk_link": 60.0,
    "primary": 60.0,
    "primary_link": 50.0,
    "secondary": 50.0,
    "secondary_link": 40.0,
    "tertiary": 40.0,
    "tertiary_link": 30.0,
    "residential": 30.0,
    "living_street": 20.0,
    "unclassified": 40.0,
    "service": 20.0,
    "track": 15.0,
    "path": 10.0,
}

# Higher = safer (major, well-lit, maintained)
_SAFETY: Dict[str, float] = {
    "motorway": 0.90,
    "motorway_link": 0.85,
    "trunk": 0.85,
    "trunk_link": 0.80,
    "primary": 0.80,
    "primary_link": 0.75,
    "secondary": 0.70,
    "secondary_link": 0.65,
    "tertiary": 0.60,
    "tertiary_link": 0.55,
    "residential": 0.50,
    "living_street": 0.55,
    "unclassified": 0.45,
    "service": 0.35,
    "track": 0.20,
    "path": 0.15,
}

# Higher = more scenic (quieter, leafier, less monotonous)
_SCENIC: Dict[str, float] = {
    "motorway": 0.05,
    "motorway_link": 0.05,
    "trunk": 0.10,
    "trunk_link": 0.10,
    "primary": 0.20,
    "primary_link": 0.20,
    "secondary": 0.35,
    "secondary_link": 0.35,
    "tertiary": 0.55,
    "tertiary_link": 0.55,
    "residential": 0.70,
    "living_street": 0.75,
    "unclassified": 0.85,
    "service": 0.40,
    "track": 0.80,
    "path": 0.90,
}

# Higher = smoother / more comfortable ride
_COMFORT: Dict[str, float] = {
    "motorway": 1.00,
    "motorway_link": 0.90,
    "trunk": 0.95,
    "trunk_link": 0.85,
    "primary": 0.85,
    "primary_link": 0.80,
    "secondary": 0.75,
    "secondary_link": 0.70,
    "tertiary": 0.65,
    "tertiary_link": 0.60,
    "residential": 0.55,
    "living_street": 0.60,
    "unclassified": 0.45,
    "service": 0.40,
    "track": 0.20,
    "path": 0.15,
}

# Higher = more fuel stations / services nearby (proxy)
_FUEL_ACCESS: Dict[str, float] = {
    "motorway": 0.85,
    "motorway_link": 0.60,
    "trunk": 0.80,
    "trunk_link": 0.60,
    "primary": 0.80,
    "primary_link": 0.65,
    "secondary": 0.65,
    "secondary_link": 0.55,
    "tertiary": 0.45,
    "tertiary_link": 0.40,
    "residential": 0.25,
    "living_street": 0.20,
    "unclassified": 0.30,
    "service": 0.35,
    "track": 0.05,
    "path": 0.05,
}

_DEFAULT_SPEED = 40.0
_DEFAULT_SAFETY = 0.50
_DEFAULT_SCENIC = 0.40
_DEFAULT_COMFORT = 0.50
_DEFAULT_FUEL = 0.50


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #

def _highway(data: Dict) -> str:
    hw = data.get("highway", "unclassified")
    if isinstance(hw, list):
        hw = hw[0]
    return str(hw)


def _parse_speed(data: Dict) -> float:
    """Extract effective speed (km/h) from edge data."""
    ms = data.get("maxspeed")
    if ms:
        try:
            s = str(ms).replace(" mph", "").replace(" kph", "").replace(" km/h", "").strip()
            v = float(s.split(";")[0])
            return v * 1.609344 if "mph" in str(ms) else v
        except (ValueError, AttributeError):
            pass
    return _SPEED_KMPH.get(_highway(data), _DEFAULT_SPEED)


def _is_toll(data: Dict) -> bool:
    return str(data.get("toll", "no")).lower() in ("yes", "true", "1")


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    total = sum(weights.values())
    if total <= 0:
        # Fallback: balanced across all dimensions
        n = len(weights)
        return {k: 1.0 / n for k in weights}
    return {k: v / total for k, v in weights.items()}


# ------------------------------------------------------------------ #
# Cost Function Generator                                             #
# ------------------------------------------------------------------ #

class CostFunctionGenerator:
    """
    Reads a constraint dict (output of ConstraintEngine) and produces
    a Python callable suitable for injection into GraphEngine algorithms.

    The generated function follows the contract:
        cost_fn(u: int, v: int, edge_data: dict) -> float

    All cost components are proportional to edge length so that the
    algorithm correctly trades off a short detour against a long cheap road.
    """

    DIMENSIONS = ("speed", "safety", "fuel_efficiency", "scenic", "comfort", "cost")

    def __init__(self, constraints: Dict[str, Any]) -> None:
        raw_weights = constraints.get("weights", {})
        # Fill any missing dimensions with 0
        filled = {d: float(raw_weights.get(d, 0.0)) for d in self.DIMENSIONS}
        self.weights = _normalize_weights(filled)
        self.avoid: List[str] = [a.lower() for a in constraints.get("avoid", [])]
        self.prefer: List[str] = [p.lower() for p in constraints.get("prefer", [])]

    def generate(self) -> Callable:
        """Return the cost callable (closure over weights/avoid/prefer)."""
        weights = self.weights
        avoid = self.avoid
        prefer = self.prefer

        def cost_fn(u: int, v: int, data: Dict) -> float:  # noqa: ARG001
            length = float(data.get("length", 1.0))
            hw = _highway(data)

            # Hard penalty for avoided road classes
            if "tolls" in avoid and _is_toll(data):
                return length * 1000.0  # effectively infinite
            if "highways" in avoid and hw in ("motorway", "motorway_link", "trunk", "trunk_link"):
                return length * 500.0
            if "unpaved" in avoid and hw in ("track", "path"):
                return length * 200.0
            if "narrow_roads" in avoid and hw in ("residential", "living_street", "service"):
                return length * 3.0
            if "busy_roads" in avoid and hw in ("motorway", "trunk", "primary"):
                return length * 4.0
            if "dark_roads" in avoid and hw in ("unclassified", "track", "path"):
                return length * 3.0

            # Preference bonuses (reduce cost)
            prefer_mult = 1.0
            if "highways" in prefer and hw in ("motorway", "trunk", "primary"):
                prefer_mult *= 0.85
            if "scenic_roads" in prefer and hw in ("unclassified", "residential", "tertiary"):
                prefer_mult *= 0.85
            if "fuel_stations" in prefer and hw in ("motorway", "trunk", "primary", "secondary"):
                prefer_mult *= 0.90
            if "lit_roads" in prefer and hw in ("motorway", "trunk", "primary", "secondary"):
                prefer_mult *= 0.90
            if "wide_roads" in prefer and hw in ("motorway", "trunk", "primary"):
                prefer_mult *= 0.85
            if "coastal_roads" in prefer and hw in ("unclassified", "secondary", "tertiary"):
                prefer_mult *= 0.80

            # Speed component: travel time in seconds (minimise)
            speed_ms = _parse_speed(data) / 3.6  # m/s
            speed_component = length / speed_ms if speed_ms > 0 else length * 10.0

            # Safety component: (1 - safety_score) * length, higher = more dangerous
            safety_score = _SAFETY.get(hw, _DEFAULT_SAFETY)
            safety_component = (1.0 - safety_score) * length

            # Fuel component: fuel ~ distance / (speed efficiency proxy)
            # Optimal speed is ~80 km/h; penalise both slow and very fast roads
            eff_speed = _parse_speed(data)
            fuel_penalty = abs(eff_speed - 80.0) / 80.0
            fuel_component = (1.0 + fuel_penalty) * length

            # Scenic component: (1 - scenic_score) * length — want scenic roads
            scenic_score = _SCENIC.get(hw, _DEFAULT_SCENIC)
            scenic_component = (1.0 - scenic_score) * length

            # Comfort component: (1 - comfort_score) * length
            comfort_score = _COMFORT.get(hw, _DEFAULT_COMFORT)
            comfort_component = (1.0 - comfort_score) * length

            # Cost component: toll penalty
            toll_cost = length * 2.0 if _is_toll(data) else 0.0
            cost_component = toll_cost + length * 0.1  # base maintenance charge

            # Normalise all components to comparable scale (per metre)
            # speed_component is in seconds; others are unitless * metres
            # Scale speed to metres by multiplying by a reference speed proxy
            norm_speed = speed_component  # already in seconds ≈ length / (40 m/s) ≈ small
            # To keep on the same order as length-based components, scale by 40 m/s
            norm_speed = norm_speed * 40.0  # back to metre-equivalent

            total = (
                weights["speed"] * norm_speed
                + weights["safety"] * safety_component
                + weights["fuel_efficiency"] * fuel_component
                + weights["scenic"] * scenic_component
                + weights["comfort"] * comfort_component
                + weights["cost"] * cost_component
            )

            return total * prefer_mult

        return cost_fn

    def describe(self) -> str:
        parts = [
            f"{dim}={w:.2f}"
            for dim, w in self.weights.items()
            if w > 0.01
        ]
        return "cost = " + " + ".join(parts)
