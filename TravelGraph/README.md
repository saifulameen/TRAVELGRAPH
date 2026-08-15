# TravelGraph – Smart Travel Planner Using Graph Algorithms

## Description

TravelGraph is a Flask-based web application that looks and feels like a
real travel/navigation product (in the spirit of Google Maps), while its
core route-planning logic is powered by a hand-written implementation of
**Dijkstra's shortest path algorithm** operating on a manually built
**weighted graph**.

Cities are modeled as graph **vertices**, and direct road connections
between them are **weighted edges** (approximate distances in km) stored
in an **adjacency list**. When a user picks a source and destination, the
app runs Dijkstra's algorithm (using a **min-heap priority queue** via
Python's `heapq`) to compute the shortest path through the city graph.
That path is then displayed on a real interactive Leaflet/OpenStreetMap
map, with **OSRM** used only to fetch realistic road geometry for each
graph edge in the path — never to replace the Dijkstra calculation
itself.

## Features

- Full-screen interactive Leaflet map (pan, zoom, markers, popups)
- Google-Maps-style Directions panel with A/B location search and swap
- Manual Dijkstra shortest-path engine (no external shortest-path libs)
- Real road-following route geometry via OSRM, with straight-line fallback
- Route info card: distance, estimated/real travel time, via-cities
- Collapsible turn-by-turn-style Route Details panel
- Dijkstra Educational page explaining the algorithm
- Interactive Dijkstra Visualizer (Play/Pause/Next/Prev/Reset) driven by
  the actual algorithm trace — never a fake animation
- Graph Explorer page: node-link diagram, adjacency list, graph stats
- About page covering graphs, weighted graphs, adjacency lists, priority
  queues, Dijkstra, and real-world applications
- Fully responsive design (desktop split-panel, mobile stacked layout)
- Optional dark mode toggle
- Graceful fallback if Nominatim/OSRM/internet is unavailable — Dijkstra
  still works on the local academic graph

## Technology Stack

**Backend:** Python 3, Flask
**Data Structures:** custom weighted graph, adjacency list, manual
Dijkstra implementation, `heapq`-based priority queue
**Frontend:** HTML5, CSS3, vanilla JavaScript (no frontend framework)
**Map:** Leaflet.js + OpenStreetMap tiles (no Google Maps API key needed)
**Geocoding:** OpenStreetMap Nominatim (best-effort, for search only)
**Road geometry:** OSRM public routing API (best-effort, for map display only)
**Database:** none — graph data lives in Python
**Auth / Payments:** none

## Architecture

```
User selects source & destination
        ↓
Flask validates cities against the academic graph
        ↓
Custom Dijkstra algorithm (graph/dijkstra.py) computes shortest city path
        ↓
For each consecutive city pair in that path, OSRM is queried for
realistic road geometry (services/routing.py)
        ↓
Combined road geometry + city path + distance/time returned as JSON
        ↓
Leaflet renders the route, A/B markers, and route info on the map
```

**Important distinction:** Dijkstra determines *which cities* the route
passes through. OSRM is only ever asked for geometry between two cities
that are already directly connected in the Dijkstra path — it never
computes the source-to-destination route itself.

## Data Structures

- **Graph:** `graph/graph_data.py` — 15 Indian cities as vertices, with
  realistic-feeling road connections as edges.
- **Adjacency List:** `GRAPH = {"Chennai": {"Vellore": 140, ...}, ...}`
- **Weighted Undirected Graph:** each edge is inserted in both directions.
- **Priority Queue:** Python's `heapq` module, storing `(distance, node)`
  tuples, giving O(log n) push/pop.

## Dijkstra Algorithm

Implemented from scratch in `graph/dijkstra.py`:

1. Initialize all distances to infinity, source to 0.
2. Push `(0, source)` onto a min-heap.
3. Pop the smallest-distance unvisited node; mark it visited.
4. Relax all outgoing edges — if a shorter path to a neighbour is found,
   update its distance and predecessor, and push it onto the heap.
5. Repeat until the destination is visited or the heap is empty.
6. Reconstruct the path by walking backwards through predecessor pointers.

The function returns the path, total distance, the order nodes were
visited in, and a full step-by-step trace used by the Dijkstra
Visualizer — so the visualization is always the *real* algorithm run,
never a canned animation.

## Map Technology

- **Leaflet.js** for the interactive map (pan/zoom/markers/popups/fit-bounds)
- **OpenStreetMap** tiles — no API key required
- **Nominatim** for location search suggestions
- **OSRM** (`router.project-osrm.org`) for road-following polylines and
  real travel durations, called once per Dijkstra path segment

## Installation (Windows)

```powershell
python -m venv venv
venv\Scripts\activate
```

If PowerShell blocks script execution, use:

```powershell
venv\Scripts\activate.bat
```

Then install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Running the Project

```powershell
python app.py
```

Open your browser to:

```
http://127.0.0.1:5000
```

## Project Structure

```
TravelGraph/
├── app.py
├── requirements.txt
├── README.md
├── graph/
│   ├── __init__.py
│   ├── graph_data.py     # cities, coordinates, adjacency-list graph
│   └── dijkstra.py       # manual Dijkstra implementation (heapq)
├── services/
│   ├── __init__.py
│   ├── geocoding.py      # Nominatim search wrapper
│   └── routing.py        # OSRM road-geometry wrapper
├── templates/
│   ├── base.html
│   ├── index.html        # homepage
│   ├── planner.html      # main map + directions panel
│   ├── graph.html        # Graph Explorer
│   ├── algorithm.html    # Dijkstra education + visualizer
│   └── about.html
└── static/
    ├── css/style.css
    └── js/
        ├── main.js       # nav + dark mode
        ├── map.js        # shared Leaflet helpers
        ├── planner.js    # directions panel + route rendering
        ├── graph.js       # Graph Explorer SVG + adjacency list
        └── algorithm.js  # Dijkstra visualizer
```

## API Endpoints

| Method | Endpoint          | Description                                              |
|--------|-------------------|------------------------------------------------------------|
| GET    | `/api/cities`     | List of supported academic-graph cities with coordinates |
| GET    | `/api/graph`      | Full graph snapshot: nodes, edges, adjacency list, stats  |
| GET    | `/api/search?q=`  | Location search (local graph cities + Nominatim results)  |
| POST   | `/api/route`      | Run Dijkstra + fetch OSRM geometry, return full route data|
| POST   | `/api/algorithm`  | Run Dijkstra only, return full step-by-step trace          |

`POST /api/route` body: `{"source": "Chennai", "destination": "Coimbatore"}`

## Complexity

- **Dijkstra with a binary heap:** O((V + E) log V), where V = number of
  cities (15) and E = number of road connections in the graph.
- **Adjacency list space complexity:** O(V + E).
- Because V and E are both small and fixed (a college-scale academic
  graph), the algorithm runs effectively instantly.

## Future Improvements

- Allow users to add custom cities/edges to the graph at runtime
- Support multiple transport modes (bus, train) with different graphs
- Cache OSRM responses to reduce external API calls
- Add A* as a comparison algorithm on the Dijkstra Visualizer page
- Persist favorite routes (would require a lightweight database)

## Viva Questions & Answers

**Q1. Why did you choose an adjacency list over an adjacency matrix?**
An adjacency list is more memory-efficient for sparse graphs like a road
network, where most cities are not directly connected to most other
cities. It's O(V + E) space instead of O(V²).

**Q2. Why does Dijkstra use a priority queue instead of scanning all
nodes for the minimum each time?**
A priority queue (min-heap) reduces the cost of repeatedly finding the
next-closest unvisited node from O(V) per lookup to O(log V) per
insertion/removal, improving overall complexity from O(V²) to
O((V+E) log V).

**Q3. Does Dijkstra work with negative edge weights?**
No. Dijkstra assumes all edge weights are non-negative, since it greedily
finalizes the shortest distance to a node once visited. All distances in
TravelGraph's graph are positive kilometer values, so this assumption
holds.

**Q4. What is the role of OSRM in this project — doesn't it compute the
shortest path too?**
OSRM is only used to fetch realistic *road geometry* (the curvy polyline
following actual roads) for each already-determined Dijkstra segment. It
is called once per consecutive city pair in the Dijkstra path — never
directly source-to-destination — so it cannot replace or override the
academic shortest-path calculation.

**Q5. What happens if OSRM or Nominatim is unavailable?**
The application degrades gracefully: Dijkstra still computes the correct
shortest city path from the local graph, and the app falls back to
straight-line segments on the map with a clear notice, rather than
crashing.

**Q6. How is the shortest path reconstructed?**
While running Dijkstra, a `previous` (predecessor) dictionary records
which node led to the shortest known distance for each node. After the
algorithm finishes, the path is reconstructed by walking backwards from
the destination through these predecessor pointers to the source, then
reversing the resulting list.

**Q7. What is the time complexity of your Dijkstra implementation?**
O((V + E) log V) using a binary heap priority queue, where V is the
number of vertices (cities) and E is the number of edges (road
connections).

**Q8. Why is the graph undirected?**
Because roads between cities can generally be traveled in either
direction, so each edge is inserted into the adjacency list in both
directions with the same weight.

**Q9. How would you extend this to a directed graph (e.g., one-way
roads)?**
Only insert the edge in one direction in the adjacency list (e.g.,
`graph[A][B] = weight` without also setting `graph[B][A] = weight`), and
Dijkstra would work unmodified since it already only follows the edges
present in the adjacency list.

**Q10. What real-world systems use Dijkstra or similar shortest-path
algorithms?**
GPS navigation systems, computer network routing protocols (like
OSPF), logistics and delivery route planning, and public transportation
routing all rely on shortest-path algorithms similar to Dijkstra.

---

*Distances in the academic graph are approximate educational values and
are not intended as official road-distance data.*
