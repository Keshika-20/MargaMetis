# MargaMetis — Intelligent Route Optimizer

Real-world road network routing on OpenStreetMap data with custom-built pathfinding algorithms, dynamic cost functions, LLM constraint extraction, and Redis caching.

**Live demo** → [marga-metis.vercel.app](https://marga-metis.vercel.app)

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
  ├── GraphManager          — OSMnx graph download + GraphML disk cache
  └── route_optimizer/intelligence/
        ├── graph_engine.py     — Dijkstra / A* / Bidirectional A* / Yen's K-Shortest
        ├── cost_function.py    — (u, v, data) → float callable, injected at traversal
        ├── constraint_engine.py — Groq LLaMA 3 NL → structured constraint JSON
        └── route_ranker.py     — multi-criteria scoring + one-sentence explanation
      │
      ▼
PostgreSQL  (user accounts, search history)
```

## Route optimisation modes

Each mode generates a cost function `(u, v, data) → float` based on real OSM `highway` tags:

| Mode | What changes |
|---|---|
| Shortest distance | Minimises `edge.length` |
| Fuel efficient | Penalises roads far from ~80 km/h optimal speed |
| Eco / Green | Fuel efficiency + prefers residential/scenic roads |
| Avoid main roads | 5× penalty on motorway/trunk/primary |
| **Smart (NL)** | Groq LLaMA 3 extracts priorities → dynamic cost weights |

### Smart route

Type a natural-language description — *"scenic route avoiding busy roads"* or *"fastest route via Tambaram"* — and the backend:

1. Sends the query to Groq LLaMA 3 (`llama-3.1-8b-instant`) with few-shot examples
2. Gets back structured JSON: priorities, avoid list, prefer list, waypoints, weights
3. Builds a `(u, v, data) → float` cost function from those weights
4. Runs A* with the cost function injected at traversal time
5. Scores the result across 6 dimensions and generates a one-sentence explanation

Falls back to rule-based extraction when no API key is set.

## Redis caching

- **Geocoding** — place name → (lat, lon) cached 24 h → eliminates Nominatim API calls
- **Route results** — full response cached 1 h → 3,500 ms → 16 ms on repeat queries

## Running locally

```bash
# optional: add free Groq key for NL constraint extraction
echo "GROQ_API_KEY=gsk_..." > .env

docker compose up -d
# → http://localhost:3030
```

First search downloads the OSMnx graph (~20 s). All subsequent searches use the GraphML cache on disk and Redis route cache.

## Stack

| | Local | Production |
|---|---|---|
| Frontend | React 18, Vite, React-Leaflet, Tailwind CSS | Vercel |
| Backend | Flask 3, SQLAlchemy, OSMnx 2, NetworkX 3, Gunicorn | Railway |
| Cache | Redis 7 | Railway Redis |
| Database | MySQL 8 | Railway PostgreSQL |
| Deployment | Docker Compose — 4 services | Railway + Vercel |

## Tests

```bash
pytest tests/test_cost_function.py -v   # 24 unit tests — cost function correctness
```

## Project structure

```
MargaMetis/
├── route_optimizer/
│   ├── intelligence/
│   │   ├── graph_engine.py      ← A* / Dijkstra / BiDir-A* / Yen's
│   │   ├── cost_function.py     ← dynamic cost callable
│   │   ├── constraint_engine.py ← Groq LLM + rule-based fallback
│   │   └── route_ranker.py      ← label + explanation
│   ├── graph/manager.py         ← OSMnx + GraphML cache
│   └── optimizer.py
├── backend/
│   └── app/
│       ├── routes/route_api.py  ← /calculate  /smart  /benchmark  /geocode
│       ├── models.py            ← User, SearchHistory
│       └── cache.py             ← Redis layer
├── frontend/src/
│   ├── pages/HomePage.jsx
│   └── components/
├── tests/test_cost_function.py
├── docker-compose.yml
└── render.yaml / railway.toml
```
