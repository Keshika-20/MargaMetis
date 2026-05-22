# MargaMetis — Intelligent Route Optimizer

Real-world road network routing on OpenStreetMap data with custom-built pathfinding algorithms, dynamic cost functions, and Redis caching.

## Algorithm Benchmark

**Chennai graph — 22,041 nodes, 55,330 edges**

| Algorithm | Query time | Nodes explored |
|---|---|---|
| Dijkstra | 60 ms | 18,954 |
| A\* (Haversine heuristic) | **13 ms** | 2,900 — **4.6× fewer** |
| Bidirectional A\* | **6 ms** | 1,470 — **12.9× fewer** |
| Yen's K-Shortest (k=3) | 800 ms | 3 diverse paths |

All four algorithms are implemented from scratch — no `nx.astar_path` or library shortcuts.

## Architecture

```
React + Leaflet
      │
      ▼
Flask REST API  ──→  Redis  (geocode cache 24h, route cache 1h)
      │
      ▼
RouteOptimizer
  ├── GraphManager      — OSMnx graph download + GraphML disk cache
  └── route_optimizer/intelligence/
        ├── graph_engine.py    — Dijkstra / A* / Bidirectional A* / Yen's K-Shortest
        ├── cost_function.py   — (u, v, data) → float callable, injected at traversal
        └── route_ranker.py    — route labelling + one-sentence explanation
      │
      ▼
MySQL  (search history per user)
```

## Route optimisation modes

Each mode generates a cost function `(u, v, data) → float` based on real OSM `highway` tags (present on 100 % of edges):

| Mode | What changes |
|---|---|
| Shortest distance | Minimises `edge.length` |
| Fuel efficient | Penalises roads far from ~80 km/h optimal speed |
| Eco / Green | Fuel efficiency + prefers residential/scenic roads |
| Avoid main roads | 5× penalty on motorway/trunk/primary — forces side streets |

## Redis caching

- **Geocoding** — place name → (lat, lon) cached 24 h → eliminates Nominatim API calls
- **Route results** — full response cached 1 h → 3,500 ms → 16 ms on repeat queries

## Running

```bash
# optional: add free Groq key for NL constraint extraction backend
echo "GROQ_API_KEY=gsk_..." > .env

docker compose up -d
# → http://localhost:3030
```

First search downloads the OSMnx graph (~20 s). All subsequent searches use the GraphML cache on disk and Redis route cache.

## Stack

| | |
|---|---|
| Frontend | React 18, Vite, React-Leaflet, Tailwind CSS |
| Backend | Flask 3, SQLAlchemy, OSMnx 2, NetworkX 3 |
| Cache | Redis 7 (geocoding + route results) |
| Database | MySQL 8 (user accounts, search history) |
| Deployment | Docker Compose — 4 services |

## Tests

```bash
pytest tests/test_cost_function.py -v   # 24 unit tests — cost function correctness
```

## Project structure

```
MargaMetis/
├── route_optimizer/
│   ├── intelligence/
│   │   ├── graph_engine.py    ← A*  /  Dijkstra  /  BiDir-A*  /  Yen's
│   │   ├── cost_function.py   ← dynamic cost callable
│   │   └── route_ranker.py    ← label + explanation
│   ├── graph/manager.py       ← OSMnx + GraphML cache
│   └── optimizer.py
├── backend/
│   └── app/
│       ├── routes/route_api.py   ← /calculate  /benchmark  /geocode
│       ├── models.py             ← User, SearchHistory
│       └── cache.py              ← Redis layer
├── frontend/src/
│   ├── pages/HomePage.jsx
│   └── components/
├── tests/test_cost_function.py
└── docker-compose.yml
```
