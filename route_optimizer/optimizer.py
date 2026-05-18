import logging
from typing import Tuple, Optional

import osmnx as ox
import networkx as nx

from .config.models import RouteConfig
from .graph.manager import GraphManager
from .intelligence.graph_engine import GraphEngine

logger = logging.getLogger(__name__)

_AVG_SPEED_KMPH = {"car": 40, "bike": 25, "bus": 30, "truck": 25, "auto": 35}


class RouteOptimizer:
    """
    Loads an OSMnx road graph and finds routes using the custom GraphEngine.
    Standard mode: pure distance A*.
    Smart mode: see route_api.py (uses full intelligence pipeline).
    """

    def __init__(self, config: Optional[RouteConfig] = None) -> None:
        self.config = config or RouteConfig()
        self.graph_manager = GraphManager(self.config)
        self.graph: Optional[nx.MultiDiGraph] = None

    def load_graph(self, center_point: Tuple[float, float], radius_m: int) -> None:
        logger.info(f"Loading graph centered at {center_point} with radius {radius_m}m...")
        self.graph = self.graph_manager.load_graph(center_point, radius_m)

    def find_route(
        self,
        origin_coords: Tuple[float, float],
        dest_coords: Tuple[float, float],
        route_type: str = "shortest",
        vehicle_type: str = "car",
    ) -> dict:
        if self.graph is None:
            raise ValueError("Graph not loaded. Call load_graph() first.")

        origin_node = ox.distance.nearest_nodes(self.graph, origin_coords[1], origin_coords[0])
        dest_node   = ox.distance.nearest_nodes(self.graph, dest_coords[1], dest_coords[0])

        engine = GraphEngine(self.graph)

        # Route-type → cost function (preset constraints)
        weight_fn = None
        if route_type != "shortest":
            from .intelligence.cost_function import CostFunctionGenerator  # noqa
            presets = {
                "fuel":       {"weights": {"fuel_efficiency": 0.75, "safety": 0.15, "speed": 0.05, "scenic": 0.03, "comfort": 0.02, "cost": 0.0}, "avoid": [], "prefer": []},
                "green":      {"weights": {"fuel_efficiency": 0.55, "scenic": 0.30, "safety": 0.10, "speed": 0.03, "comfort": 0.02, "cost": 0.0}, "avoid": [], "prefer": ["scenic_roads"]},
                # avoid_main: penalises motorway/trunk/primary — routes through secondary/residential streets
                "avoid_main": {"weights": {"scenic": 0.45, "comfort": 0.25, "safety": 0.20, "speed": 0.05, "fuel_efficiency": 0.03, "cost": 0.02}, "avoid": ["highways"], "prefer": ["scenic_roads"]},
            }
            if route_type in presets:
                weight_fn = CostFunctionGenerator(presets[route_type]).generate()

        result = engine.astar(origin_node, dest_node, weight_fn)
        if result["path"] is None:
            raise ValueError("No path found between these locations.")

        speed = _AVG_SPEED_KMPH.get(vehicle_type, 40)
        eta_min = round((result["distance"] / 1000 / speed) * 60, 2)

        return {
            "path":              result["path"],
            "distance_m":        round(result["distance"], 2),
            "estimated_time_min": eta_min,
            "algorithm_time_ms": round(result["time_ms"], 3),
            "nodes_explored":    result["nodes_explored"],
        }
