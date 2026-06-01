import logging
from typing import Tuple, Optional

import osmnx as ox
import networkx as nx

from .config.models import RouteConfig
from .graph.manager import GraphManager
from .core.pathfinder import AStarPathfinder, RouteResult
from .confidence_scorer import RouteConfidenceScorer   # ← moved to top

logger = logging.getLogger(__name__)


class RouteOptimizer:
    """
    High-level class to manage road network graphs and compute shortest routes
    using A* pathfinding on OSMnx road networks.
    """

    def __init__(self, config: Optional[RouteConfig] = None) -> None:
        self.config: RouteConfig = config or RouteConfig()
        self.graph_manager: GraphManager = GraphManager(self.config)
        self.graph: Optional[nx.MultiDiGraph] = None

    def load_graph(self, center_point: Tuple[float, float], radius_m: int) -> None:
        logger.info(f"Loading graph centered at {center_point} with radius {radius_m} meters...")
        self.graph = self.graph_manager.load_graph(center_point, radius_m)

    def find_shortest_route(
        self,
        origin_coords: Tuple[float, float],
        dest_coords: Tuple[float, float],
        departure_hour: int = 12,          # ← new param, defaults to noon
    ) -> RouteResult:
        """
        Find the shortest path between origin and destination coordinates.

        Args:
            origin_coords:   (lat, lon) of start point.
            dest_coords:     (lat, lon) of end point.
            departure_hour:  Hour of departure in 24h format (0–23).
                             Used by the confidence scorer to factor in
                             rush-hour risk. Defaults to 12 (noon).

        Returns:
            RouteResult with path, distance, and confidence_result attached.

        Raises:
            ValueError: If the graph has not been loaded yet.
        """
        if self.graph is None:
            raise ValueError("Graph not loaded. Call `load_graph()` first.")

        # ── 1. Find nearest graph nodes ──────────────────────────────
        start_node = ox.distance.nearest_nodes(
            self.graph, origin_coords[1], origin_coords[0]
        )
        end_node = ox.distance.nearest_nodes(
            self.graph, dest_coords[1], dest_coords[0]
        )
        logger.info(f"Nearest nodes: Start={start_node}, End={end_node}")

        # ── 2. Run A* ────────────────────────────────────────────────
        pathfinder = AStarPathfinder(
            self.graph, enable_logging=True, show_progress=True
        )
        result = pathfinder.find_shortest_path(start_node, end_node)
        logger.info(
            f"Shortest path found: {result.path} "
            f"(Distance: {result.distance_m:.2f} m)"
        )

        # ── 3. Score the route's reliability ─────────────────────────
        scorer = RouteConfidenceScorer(self.graph)   # self.graph, not graph
        result.confidence_result = scorer.score(
            route_nodes=result.path,                 # result.path, not routes
            departure_hour=departure_hour,           # the param we added above
        )
        logger.info(
            f"Confidence: {result.confidence_result.confidence}% "
            f"({result.confidence_result.risk_level} risk)"
        )

        return result