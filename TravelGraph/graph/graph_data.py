"""
graph_data.py

Defines the academic weighted graph for TravelGraph.

Cities are vertices. Roads/connections are edges. The edge weight
represents an approximate educational distance in kilometers between
two directly-connected cities.

IMPORTANT (see README / About page):
Distances in this academic graph are approximate educational values
and are NOT intended as official road-distance data. They exist so
that Dijkstra's algorithm has a real weighted graph to operate on.

The graph is represented as an adjacency list:

    graph = {
        "CityA": {"CityB": weight, "CityC": weight, ...},
        ...
    }

Because this is an undirected graph (you can travel either direction
along a road), every edge is inserted in both directions.
"""

# Latitude/longitude for each supported city (used for map markers
# and for geocoding fallback / display purposes).
CITY_COORDINATES = {
    "Chennai":     {"lat": 13.0827, "lon": 80.2707},
    "Vellore":     {"lat": 12.9165, "lon": 79.1325},
    "Bangalore":   {"lat": 12.9716, "lon": 77.5946},
    "Mysore":      {"lat": 12.2958, "lon": 76.6394},
    "Salem":       {"lat": 11.6643, "lon": 78.1460},
    "Erode":       {"lat": 11.3410, "lon": 77.7172},
    "Tiruppur":    {"lat": 11.1085, "lon": 77.3411},
    "Coimbatore":  {"lat": 11.0168, "lon": 76.9558},
    "Madurai":     {"lat": 9.9252,  "lon": 78.1198},
    "Trichy":      {"lat": 10.7905, "lon": 78.7047},
    "Thanjavur":   {"lat": 10.7870, "lon": 79.1378},
    "Pondicherry": {"lat": 11.9416, "lon": 79.8083},
    "Kochi":       {"lat": 9.9312,  "lon": 76.2673},
    "Kozhikode":   {"lat": 11.2588, "lon": 75.7804},
    "Hyderabad":   {"lat": 17.3850, "lon": 78.4867},
}

# Raw undirected edge list: (cityA, cityB, approximate_km)
# These roughly correspond to real highway connectivity between the
# cities so that the resulting shortest paths feel plausible.
_RAW_EDGES = [
    ("Chennai", "Vellore", 140),
    ("Chennai", "Pondicherry", 160),
    ("Chennai", "Salem", 340),
    ("Vellore", "Bangalore", 210),
    ("Vellore", "Salem", 175),
    ("Bangalore", "Mysore", 145),
    ("Bangalore", "Salem", 190),
    ("Bangalore", "Hyderabad", 570),
    ("Mysore", "Kozhikode", 235),
    ("Mysore", "Coimbatore", 210),
    ("Salem", "Erode", 65),
    ("Salem", "Trichy", 135),
    ("Salem", "Coimbatore", 165),
    ("Erode", "Tiruppur", 45),
    ("Erode", "Coimbatore", 60),
    ("Tiruppur", "Coimbatore", 50),
    ("Coimbatore", "Kochi", 190),
    ("Coimbatore", "Madurai", 215),
    ("Kochi", "Kozhikode", 190),
    ("Madurai", "Trichy", 130),
    ("Madurai", "Thanjavur", 155),
    ("Trichy", "Thanjavur", 60),
    ("Trichy", "Pondicherry", 190),
    ("Thanjavur", "Pondicherry", 175),
    ("Pondicherry", "Salem", 250),
    ("Hyderabad", "Chennai", 630),
]


def _build_graph():
    """Build an undirected adjacency-list graph from the raw edge list."""
    g = {city: {} for city in CITY_COORDINATES}
    for a, b, weight in _RAW_EDGES:
        g[a][b] = weight
        g[b][a] = weight
    return g


# The adjacency-list weighted graph used throughout the app.
GRAPH = _build_graph()


def get_city_list():
    """Return a sorted list of all supported city names."""
    return sorted(CITY_COORDINATES.keys())


def get_city_coordinates(city_name):
    """Return {'lat':..., 'lon':...} for a supported city, or None."""
    return CITY_COORDINATES.get(city_name)


def is_supported_city(city_name):
    """Case-sensitive membership check against the academic graph."""
    return city_name in CITY_COORDINATES


def get_edge_count():
    """Return the number of unique undirected edges in the graph."""
    return len(_RAW_EDGES)


def get_graph_snapshot():
    """
    Return a JSON-serializable snapshot of the graph: nodes, edges,
    and adjacency list, used by the Graph Explorer page.
    """
    nodes = []
    for city, coords in CITY_COORDINATES.items():
        nodes.append({
            "id": city,
            "lat": coords["lat"],
            "lon": coords["lon"],
            "degree": len(GRAPH[city]),
        })

    edges = []
    seen = set()
    for a, b, weight in _RAW_EDGES:
        key = tuple(sorted([a, b]))
        if key in seen:
            continue
        seen.add(key)
        edges.append({"source": a, "target": b, "weight": weight})

    return {
        "nodes": nodes,
        "edges": edges,
        "adjacency_list": GRAPH,
        "vertex_count": len(nodes),
        "edge_count": len(edges),
    }
