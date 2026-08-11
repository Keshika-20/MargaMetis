"""
Hand-written JSON Schemas describing MargaMetis's public API contract.
Used by tests/spec/test_api_spec.py to catch accidental breaking changes to
response shapes. This is the closest thing the project has to an OpenAPI
spec today -- treat edits here as an explicit, reviewed API contract change.
"""

HEALTH_RESPONSE = {
    "type": "object",
    "required": ["status", "service", "cache"],
    "properties": {
        "status": {"type": "string"},
        "service": {"type": "string"},
        "cache": {"type": "object", "required": ["status", "hits", "misses", "hit_rate_pct"]},
    },
}

ERROR_RESPONSE = {
    "type": "object",
    "required": ["error"],
    "properties": {
        "error": {"type": "string"},
    },
}

ORIGIN_DEST = {
    "type": "object",
    "required": ["name", "lat", "lon"],
    "properties": {
        "name": {"type": "string"},
        "lat": {"type": "number"},
        "lon": {"type": "number"},
    },
}

ROUTE_CALCULATE_RESPONSE = {
    "type": "object",
    "required": [
        "success", "cache_hit", "distance_km", "distance_m",
        "path_nodes", "origin", "destination", "path_coordinates",
        "estimated_time_min", "route_type", "vehicle_type",
    ],
    "properties": {
        "success": {"type": "boolean"},
        "cache_hit": {"type": "boolean"},
        "distance_km": {"type": "number"},
        "distance_m": {"type": "number"},
        "path_nodes": {"type": "integer"},
        "origin": ORIGIN_DEST,
        "destination": ORIGIN_DEST,
        "path_coordinates": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["lat", "lon"],
                "properties": {"lat": {"type": "number"}, "lon": {"type": "number"}},
            },
        },
        "estimated_time_min": {"type": "number"},
        "route_type": {"type": "string"},
        "vehicle_type": {"type": "string"},
    },
}

SMART_ROUTE_ITEM = {
    "type": "object",
    "required": [
        "route_id", "label", "rank", "distance_m", "eta_min",
        "score", "semantic_class", "semantic_confidence",
        "explanation", "path_coordinates",
    ],
    "properties": {
        "route_id": {"type": "string"},
        "label": {"type": "string"},
        "rank": {"type": "integer"},
        "distance_m": {"type": "number"},
        "eta_min": {"type": "number"},
        "score": {
            "type": "object",
            "required": ["speed", "safety", "scenic", "comfort", "fuel_access", "toll_cost", "composite"],
        },
        "semantic_class": {"type": "string"},
        "semantic_confidence": {"type": "number"},
        "explanation": {"type": "string"},
        "path_coordinates": {"type": "array"},
    },
}

ROUTE_SMART_RESPONSE = {
    "type": "object",
    "required": ["success", "routes", "constraints", "cost_formula", "origin", "destination"],
    "properties": {
        "success": {"type": "boolean"},
        "routes": {"type": "array", "items": SMART_ROUTE_ITEM},
        "constraints": {
            "type": "object",
            "required": ["weights", "avoid", "prefer", "vehicle_type"],
        },
        "cost_formula": {"type": "string"},
        "origin": ORIGIN_DEST,
        "destination": ORIGIN_DEST,
    },
}

BENCHMARK_ALGO_RESULT = {
    "type": "object",
    "required": ["time_ms", "distance", "nodes_explored", "path_length"],
    "properties": {
        "time_ms": {"type": "number"},
        "distance": {"type": ["number", "null"]},
        "nodes_explored": {"type": "integer"},
        "path_length": {"type": "integer"},
    },
}

ROUTE_BENCHMARK_RESPONSE = {
    "type": "object",
    "required": ["success", "origin", "destination", "graph_nodes", "graph_edges", "results"],
    "properties": {
        "success": {"type": "boolean"},
        "origin": ORIGIN_DEST,
        "destination": ORIGIN_DEST,
        "graph_nodes": {"type": "integer"},
        "graph_edges": {"type": "integer"},
        "results": {
            "type": "object",
            "required": ["dijkstra", "astar", "bidirectional_astar", "yen_k_shortest"],
            "properties": {
                "dijkstra": BENCHMARK_ALGO_RESULT,
                "astar": BENCHMARK_ALGO_RESULT,
                "bidirectional_astar": BENCHMARK_ALGO_RESULT,
                "yen_k_shortest": {
                    "type": "object",
                    "required": ["time_ms", "paths_found", "distances"],
                },
            },
        },
    },
}
