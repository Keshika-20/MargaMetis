"""
A4 — Multi-Route Ranking + Explainability
Scores K routes across 6 dimensions, assigns labels, and generates a
one-sentence explanation per route using rule-based templates + score values.

Score dimensions (all 0–1, higher = better for the user):
  speed          — inverse travel-time estimate
  safety         — weighted average of highway safety scores
  fuel_access    — proxy for fuel stations / services along route
  comfort        — road-surface quality proxy
  scenic         — quiet / leafy road mix
  toll_cost      — 1 if no tolls, decreasing with toll exposure
"""

from typing import Any, Dict, List, Optional

import networkx as nx

from .cost_function import (
    _COMFORT,
    _DEFAULT_COMFORT,
    _DEFAULT_FUEL,
    _DEFAULT_SAFETY,
    _DEFAULT_SCENIC,
    _DEFAULT_SPEED,
    _FUEL_ACCESS,
    _SAFETY,
    _SCENIC,
    _SPEED_KMPH,
    _highway,
    _is_toll,
    _parse_speed,
)

# Route labels in priority order
_LABELS = [
    "Fastest",
    "Safest",
    "Most Scenic",
    "Most Fuel-Efficient",
    "Balanced",
    "Cheapest",
]

# Explanation templates  (label → template string)
# {time_min}, {safety_pct}, {scenic_pct}, {toll_status}, {road_mix} are filled at runtime
_TEMPLATES: Dict[str, str] = {
    "Fastest": (
        "This route minimises travel time at ~{time_min} min using primarily "
        "{road_mix} roads — {time_delta} the average."
    ),
    "Safest": (
        "This route scores {safety_pct}% on safety, favouring {road_mix} "
        "roads{toll_status}."
    ),
    "Most Scenic": (
        "This route scores {scenic_pct}% scenic, passing through {road_mix} "
        "streets with an estimated travel time of ~{time_min} min."
    ),
    "Most Fuel-Efficient": (
        "This route is optimised for fuel efficiency ({fuel_pct}% score) via "
        "{road_mix} roads{toll_status}."
    ),
    "Balanced": (
        "A balanced route (~{time_min} min, {safety_pct}% safe, {scenic_pct}% "
        "scenic) offering the best composite score across all preferences."
    ),
    "Cheapest": (
        "This toll-free route costs the least{toll_status} with ~{time_min} min "
        "travel time on {road_mix} roads."
    ),
}


class RouteRanker:
    """
    Scores and labels a list of route dicts (output of GraphEngine.yen_k_shortest).
    Attaches 'scores', 'label', 'explanation', and 'rank' fields in-place.
    """

    def __init__(self, graph: nx.MultiDiGraph) -> None:
        self.graph = graph

    # ------------------------------------------------------------------ #
    # Public API                                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _deduplicate(routes: List[Dict]) -> List[Dict]:
        """Remove routes that are within 3% distance AND 2% composite of an already-kept route."""
        kept: List[Dict] = []
        for r in routes:
            dist_r = r.get("distance", 0)
            comp_r = r.get("scores", {}).get("composite", 0)
            is_dup = any(
                dist_r > 0 and abs(dist_r - k.get("distance", 0)) / dist_r < 0.03
                and abs(comp_r - k.get("scores", {}).get("composite", 0)) < 0.02
                for k in kept
            )
            if not is_dup:
                kept.append(r)
        return kept

    def rank_routes(
        self,
        routes: List[Dict],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> List[Dict]:
        """
        Score every route, deduplicate near-identical paths, assign unique
        labels, generate explanations, and return sorted by composite score.
        """
        if not routes:
            return []

        weights = (constraints or {}).get("weights", {})

        # Score all routes
        for route in routes:
            route["scores"] = self._score_route(route["path"])

        # Remove near-identical routes before labelling
        routes = self._deduplicate(routes)

        # Assign labels (each label used at most once)
        self._assign_labels(routes, weights)

        # Generate explanations
        avg_time = sum(
            r["scores"].get("speed_time_min", 30.0) for r in routes
        ) / len(routes)
        for route in routes:
            route["explanation"] = self._explain(route, avg_time)

        # Sort by composite score
        routes.sort(key=lambda r: -r["scores"].get("composite", 0.0))
        for i, r in enumerate(routes):
            r["rank"] = i + 1

        return routes

    # ------------------------------------------------------------------ #
    # Scoring                                                             #
    # ------------------------------------------------------------------ #

    def _score_route(self, path: List[int]) -> Dict[str, float]:
        if len(path) < 2:
            return self._zero_scores()

        total_length = 0.0
        total_time_s = 0.0
        safety_sum = 0.0
        scenic_sum = 0.0
        comfort_sum = 0.0
        fuel_sum = 0.0
        toll_length = 0.0
        road_type_lengths: Dict[str, float] = {}

        for i in range(len(path) - 1):
            edge_dict = self.graph.get_edge_data(path[i], path[i + 1])
            if not edge_dict:
                continue
            # Pick the edge with shortest length
            data = min(edge_dict.values(), key=lambda d: d.get("length", float("inf")))
            length = float(data.get("length", 0.0))
            total_length += length

            hw = _highway(data)
            road_type_lengths[hw] = road_type_lengths.get(hw, 0.0) + length

            speed_ms = _parse_speed(data) / 3.6
            total_time_s += length / speed_ms if speed_ms > 0 else length / (_DEFAULT_SPEED / 3.6)

            safety_sum += _SAFETY.get(hw, _DEFAULT_SAFETY) * length
            scenic_sum += _SCENIC.get(hw, _DEFAULT_SCENIC) * length
            comfort_sum += _COMFORT.get(hw, _DEFAULT_COMFORT) * length
            fuel_sum += _FUEL_ACCESS.get(hw, _DEFAULT_FUEL) * length

            if _is_toll(data):
                toll_length += length

        if total_length <= 0:
            return self._zero_scores()

        time_min = total_time_s / 60.0

        # Normalise to 0-1 using soft caps
        speed_score = max(0.0, 1.0 - time_min / 120.0)   # 120 min cap
        safety_score = safety_sum / total_length
        scenic_score = scenic_sum / total_length
        comfort_score = comfort_sum / total_length
        fuel_score = fuel_sum / total_length
        toll_score = 1.0 - (toll_length / total_length)

        # Top road type for explanation
        dominant_hw = max(road_type_lengths, key=road_type_lengths.get) if road_type_lengths else "road"

        return {
            "speed": round(speed_score, 3),
            "safety": round(safety_score, 3),
            "scenic": round(scenic_score, 3),
            "comfort": round(comfort_score, 3),
            "fuel_access": round(fuel_score, 3),
            "toll_cost": round(toll_score, 3),
            "speed_time_min": round(time_min, 1),
            "total_length_m": round(total_length, 1),
            "toll_free": toll_length == 0.0,
            "dominant_highway": dominant_hw,
            "composite": round(
                (speed_score + safety_score + scenic_score + comfort_score
                 + fuel_score + toll_score) / 6.0,
                3,
            ),
        }

    @staticmethod
    def _zero_scores() -> Dict[str, float]:
        return {d: 0.0 for d in
                ("speed", "safety", "scenic", "comfort", "fuel_access",
                 "toll_cost", "composite")} | {
            "speed_time_min": 0.0,
            "total_length_m": 0.0,
            "toll_free": True,
            "dominant_highway": "road",
        }

    # ------------------------------------------------------------------ #
    # Label assignment                                                    #
    # ------------------------------------------------------------------ #

    def _assign_labels(
        self, routes: List[Dict], weights: Dict[str, float]
    ) -> None:
        used_labels: set = set()

        # Dimension → score key mapping
        dim_to_score = {
            "speed": "speed",
            "safety": "safety",
            "scenic": "scenic",
            "fuel_efficiency": "fuel_access",
            "comfort": "comfort",
            "cost": "toll_cost",
        }
        label_for_dim = {
            "speed": "Fastest",
            "safety": "Safest",
            "scenic": "Most Scenic",
            "fuel_efficiency": "Most Fuel-Efficient",
            "cost": "Cheapest",
            "comfort": "Balanced",
        }

        # Sort dims by user's weight preference
        ordered_dims = sorted(dim_to_score, key=lambda d: -weights.get(d, 0.0))

        # Assign the top-scoring route for each label
        for dim in ordered_dims:
            score_key = dim_to_score[dim]
            label = label_for_dim[dim]
            if label in used_labels:
                continue
            best = max(routes, key=lambda r: r["scores"].get(score_key, 0.0))
            if "label" not in best:
                best["label"] = label
                used_labels.add(label)

        # Remaining unlabelled routes get "Balanced" or ordinal fallback
        fallback_idx = 2
        for route in routes:
            if "label" not in route:
                if "Balanced" not in used_labels:
                    route["label"] = "Balanced"
                    used_labels.add("Balanced")
                else:
                    route["label"] = f"Alternative {fallback_idx}"
                    fallback_idx += 1

    # ------------------------------------------------------------------ #
    # Explanation                                                         #
    # ------------------------------------------------------------------ #

    def _explain(self, route: Dict, avg_time_min: float) -> str:
        scores = route["scores"]
        label = route.get("label", "Balanced")
        time_min = scores.get("speed_time_min", 0.0)
        dominant = scores.get("dominant_highway", "road")

        road_map = {
            "motorway": "motorway",
            "trunk": "trunk",
            "primary": "primary",
            "secondary": "secondary",
            "tertiary": "tertiary",
            "residential": "residential",
            "unclassified": "unclassified",
            "service": "service",
        }
        road_mix = road_map.get(dominant, dominant)

        toll_status = "" if scores.get("toll_free", True) else ", with minor toll exposure"

        time_delta = ""
        if avg_time_min > 0:
            diff_pct = (time_min - avg_time_min) / avg_time_min * 100
            if diff_pct < -5:
                time_delta = f"{abs(diff_pct):.0f}% faster than"
            elif diff_pct > 5:
                time_delta = f"{abs(diff_pct):.0f}% slower than"
            else:
                time_delta = "comparable to"

        template = _TEMPLATES.get(label, _TEMPLATES["Balanced"])
        return template.format(
            time_min=f"{time_min:.0f}",
            safety_pct=f"{scores.get('safety', 0) * 100:.0f}",
            scenic_pct=f"{scores.get('scenic', 0) * 100:.0f}",
            fuel_pct=f"{scores.get('fuel_access', 0) * 100:.0f}",
            toll_status=toll_status,
            road_mix=road_mix,
            time_delta=time_delta,
        )
