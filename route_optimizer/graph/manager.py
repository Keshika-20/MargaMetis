import os
import logging
from typing import Tuple

import osmnx as ox
import networkx as nx

from ..config.models import RouteConfig

logger = logging.getLogger(__name__)


class GraphManager:

    def __init__(self, config: RouteConfig) -> None:
        self.config = config
        os.makedirs(self.config.graph_cache_dir, exist_ok=True)

    def load_graph(self, center_point: Tuple[float, float], radius_m: int) -> nx.MultiDiGraph:
        cache_name = f"graph_{center_point[0]:.6f}_{center_point[1]:.6f}_{radius_m}.graphml"
        cache_file = os.path.join(self.config.graph_cache_dir, cache_name)

        if os.path.exists(cache_file):
            logger.info(f"Loading graph from disk cache: {cache_file}")
            try:
                return ox.load_graphml(cache_file)
            except Exception as e:
                logger.error(f"Cached graph corrupt, re-downloading: {e}")

        return self._download_graph(center_point, radius_m, cache_file)

    def _download_graph(
        self, center_point: Tuple[float, float], radius_m: int, cache_file: str
    ) -> nx.MultiDiGraph:
        logger.info(f"Downloading road network at {center_point}, radius {radius_m}m")
        try:
            graph = ox.graph_from_point(center_point, dist=radius_m, network_type='drive', simplify=True)
            ox.save_graphml(graph, cache_file)
            logger.info(f"Graph cached at {cache_file}")
            return graph
        except Exception as e:
            logger.error(f"Graph download failed: {e}")
            raise
