import math
import networkx as nx
from typing import Tuple, Dict

def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def get_node_coords(graph: nx.MultiDiGraph, node: int) -> Tuple[float, float]:
    return (graph.nodes[node]['y'], graph.nodes[node]['x'])

def estimate_travel_time(distance_m: float) -> Dict[str, float]:
    """
    Estimate travel time for different modes of transport (in minutes).

    Args:
        distance_m (float): Distance in meters.

    Returns:
        Dict[str, float]: Estimated travel times in minutes for car, bike, and walk.
    """
    speeds = {
        "Car": 40.0,     # km/h
        "Bike": 20.0,    # km/h
        "Walk": 5.0      # km/h
    }

    times = {}
    for mode, speed in speeds.items():
        speed_m_s = speed * 1000 / 3600  # km/h → m/s
        time_s = distance_m / speed_m_s
        times[mode] = time_s / 60        # seconds → minutes

    return times
