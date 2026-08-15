"""
app.py

TravelGraph — Smart Travel Planner Using Graph Algorithms.

Flask backend that serves the web pages and JSON APIs. The core
academic shortest-path calculation is performed by a hand-written
Dijkstra implementation (graph/dijkstra.py) operating on a manually
defined weighted adjacency-list graph (graph/graph_data.py).

External services (Nominatim for search, OSRM for road geometry) are
used only for geographic convenience and map visualization — never
for the shortest-path calculation itself.
"""

import math
import traceback

from flask import Flask, jsonify, render_template, request

from graph.graph_data import (
    GRAPH,
    get_city_list,
    get_city_coordinates,
    is_supported_city,
    get_edge_count,
    get_graph_snapshot,
    CITY_COORDINATES,
)
from graph.dijkstra import dijkstra_shortest_path
from services.geocoding import search_locations
from services.routing import get_multi_segment_geometry

app = Flask(__name__)

# Average assumed travel speed (km/h) used ONLY as a fallback when
# OSRM duration data is not available for a segment. This is clearly
# labeled "Estimated travel time" everywhere it's shown.
FALLBACK_AVERAGE_SPEED_KMH = 55


# ---------------------------------------------------------------------------
# Page routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html", active_page="home")


@app.route("/planner")
def planner():
    return render_template(
        "planner.html",
        active_page="planner",
        cities=get_city_list(),
    )


@app.route("/graph-explorer")
def graph_explorer():
    return render_template(
        "graph.html",
        active_page="graph",
        cities=get_city_list(),
        edge_count=get_edge_count(),
    )


@app.route("/algorithm")
def algorithm_page():
    return render_template(
        "algorithm.html",
        active_page="algorithm",
        cities=get_city_list(),
    )


@app.route("/about")
def about():
    return render_template("about.html", active_page="about")


# ---------------------------------------------------------------------------
# API routes
# ---------------------------------------------------------------------------

@app.route("/api/cities", methods=["GET"])
def api_cities():
    """Return the list of supported academic-graph cities with coordinates."""
    cities = []
    for name in get_city_list():
        coords = get_city_coordinates(name)
        cities.append({"name": name, "lat": coords["lat"], "lon": coords["lon"]})
    return jsonify({"success": True, "cities": cities})


@app.route("/api/graph", methods=["GET"])
def api_graph():
    """Return the full graph snapshot: nodes, edges, adjacency list, stats."""
    try:
        snapshot = get_graph_snapshot()
        return jsonify({
            "success": True,
            "vertices": snapshot["vertex_count"],
            "edges": snapshot["edge_count"],
            "graph_type": "Weighted Undirected Graph",
            "representation": "Adjacency List",
            "priority_queue": "Min Heap (Python heapq)",
            "algorithm": "Dijkstra's Shortest Path",
            "nodes": snapshot["nodes"],
            "edge_list": snapshot["edges"],
            "adjacency_list": snapshot["adjacency_list"],
        })
    except Exception:
        app.logger.error("Error building graph snapshot:\n%s", traceback.format_exc())
        return jsonify({"success": False, "error": "Unable to load graph data."}), 500


@app.route("/api/search", methods=["GET"])
def api_search():
    """
    Location search autocomplete, used by the Directions search boxes.

    Merges results from the local academic city list (always available)
    with live Nominatim results (best-effort). Each result is tagged
    with `in_graph` so the frontend can distinguish supported academic
    cities from general geocoded places.
    """
    query = request.args.get("q", "").strip()

    if len(query) < 2:
        return jsonify({"success": True, "results": []})

    results = []

    # Local academic cities first (these always work with Dijkstra).
    query_lower = query.lower()
    for name in get_city_list():
        if query_lower in name.lower():
            coords = get_city_coordinates(name)
            results.append({
                "name": name,
                "lat": coords["lat"],
                "lon": coords["lon"],
                "in_graph": True,
            })

    # Then augment with live Nominatim results (best-effort; may be empty).
    try:
        nominatim_results = search_locations(query, limit=5)
        existing_names = {r["name"] for r in results}
        for loc in nominatim_results:
            if loc["name"] in existing_names:
                continue
            results.append({
                "name": loc["name"],
                "lat": loc["lat"],
                "lon": loc["lon"],
                "in_graph": is_supported_city(loc["name"]),
            })
    except Exception:
        # Nominatim being unreachable should never break search.
        app.logger.warning("Nominatim search failed:\n%s", traceback.format_exc())

    return jsonify({"success": True, "results": results[:10]})


@app.route("/api/route", methods=["POST"])
def api_route():
    """
    Core route-planning endpoint.

    Request JSON:  {"source": "Chennai", "destination": "Coimbatore"}

    Flow:
        1. Validate input.
        2. Confirm both cities exist in the academic graph.
        3. Run the manual Dijkstra implementation.
        4. Fetch OSRM road geometry for each segment of the resulting
           path (best-effort; falls back to straight lines on failure).
        5. Compute distance / estimated travel time.
        6. Return a structured JSON response.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid or missing JSON body."}), 400

        source = (data.get("source") or "").strip()
        destination = (data.get("destination") or "").strip()

        if not source:
            return jsonify({"success": False, "error": "Please choose a starting location."}), 400
        if not destination:
            return jsonify({"success": False, "error": "Please choose a destination."}), 400
        if source == destination:
            return jsonify({"success": False, "error": "Source and destination cannot be the same city."}), 400

        if not is_supported_city(source):
            return jsonify({
                "success": False,
                "error": (
                    f'"{source}" is not part of the current academic city graph. '
                    f"TravelGraph currently supports {len(CITY_COORDINATES)} cities — "
                    "please pick a starting location from the suggested list."
                ),
            }), 400

        if not is_supported_city(destination):
            return jsonify({
                "success": False,
                "error": (
                    f'"{destination}" is not part of the current academic city graph. '
                    f"TravelGraph currently supports {len(CITY_COORDINATES)} cities — "
                    "please pick a destination from the suggested list."
                ),
            }), 400

        # --- Run the manual Dijkstra algorithm ---
        result = dijkstra_shortest_path(GRAPH, source, destination)

        if not result["success"]:
            return jsonify({
                "success": False,
                "error": result.get("error") or "No route could be found between these cities.",
            }), 404

        path = result["path"]
        distance_km = result["distance"]

        # --- Build per-segment academic distances (for the route panel) ---
        segment_summaries = []
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            segment_summaries.append({
                "from": a,
                "to": b,
                "distance_km": GRAPH[a][b],
            })

        # --- Fetch OSRM road geometry for each segment (best-effort) ---
        osrm_result = get_multi_segment_geometry(path, CITY_COORDINATES)

        # --- Determine displayed distance & duration ---
        # Prefer OSRM's real road distance/duration when every segment
        # succeeded; otherwise fall back to the academic graph distance
        # and an estimated travel time based on average speed.
        if osrm_result["all_segments_ok"]:
            total_osrm_distance_km = sum(
                (seg["distance_meters"] or 0) / 1000 for seg in osrm_result["segments"]
            )
            total_osrm_duration_min = sum(
                (seg["duration_seconds"] or 0) / 60 for seg in osrm_result["segments"]
            )
            display_distance_km = round(total_osrm_distance_km, 1)
            display_duration_min = round(total_osrm_duration_min)
            duration_is_estimated = False
        else:
            display_distance_km = round(distance_km, 1)
            display_duration_min = round((distance_km / FALLBACK_AVERAGE_SPEED_KMH) * 60)
            duration_is_estimated = True

        road_geometry_available = osrm_result["success"]

        response = {
            "success": True,
            "source": source,
            "destination": destination,
            "path": path,
            "academic_distance_km": round(distance_km, 1),
            "display_distance_km": display_distance_km,
            "display_duration_minutes": display_duration_min,
            "duration_is_estimated": duration_is_estimated,
            "via_cities": path[1:-1],
            "city_count": len(path),
            "segment_count": len(path) - 1,
            "segments": segment_summaries,
            "visited_nodes": result["visited_nodes"],
            "algorithm_steps": result["algorithm_steps"],
            "road_geometry_available": road_geometry_available,
            "road_geometry_fully_available": osrm_result["all_segments_ok"],
            "route_geometry": osrm_result["combined_geometry"],
            "route_segments_geometry": osrm_result["segments"],
            "markers": {
                "source": get_city_coordinates(source),
                "destination": get_city_coordinates(destination),
                "waypoints": [
                    {"name": city, **get_city_coordinates(city)}
                    for city in path[1:-1]
                ],
            },
        }

        if not road_geometry_available:
            response["notice"] = "Road visualization is temporarily unavailable. Showing the Dijkstra city route instead."

        return jsonify(response)

    except Exception:
        app.logger.error("Error in /api/route:\n%s", traceback.format_exc())
        return jsonify({
            "success": False,
            "error": "Something went wrong while calculating the route. Please try again.",
        }), 500


@app.route("/api/algorithm", methods=["POST"])
def api_algorithm():
    """
    Run Dijkstra and return the FULL step-by-step trace, used by the
    Dijkstra Visualizer page. This calls the exact same algorithm
    implementation as /api/route — the visualization is never faked.
    """
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({"success": False, "error": "Invalid or missing JSON body."}), 400

        source = (data.get("source") or "").strip()
        destination = (data.get("destination") or "").strip()

        if not source or not destination:
            return jsonify({"success": False, "error": "Please select both a source and destination city."}), 400
        if source == destination:
            return jsonify({"success": False, "error": "Source and destination cannot be the same city."}), 400
        if not is_supported_city(source) or not is_supported_city(destination):
            return jsonify({"success": False, "error": "Please select cities from the supported academic graph."}), 400

        result = dijkstra_shortest_path(GRAPH, source, destination)

        if not result["success"]:
            return jsonify({
                "success": False,
                "error": result.get("error") or "No path exists between these cities.",
            }), 404

        return jsonify({
            "success": True,
            "source": source,
            "destination": destination,
            "path": result["path"],
            "distance": round(result["distance"], 1),
            "visited_nodes": result["visited_nodes"],
            "algorithm_steps": result["algorithm_steps"],
            "total_steps": len(result["algorithm_steps"]),
        })

    except Exception:
        app.logger.error("Error in /api/algorithm:\n%s", traceback.format_exc())
        return jsonify({"success": False, "error": "Something went wrong running the algorithm."}), 500


# ---------------------------------------------------------------------------
# Error handlers — never expose stack traces to the user
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def handle_404(_error):
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Endpoint not found."}), 404
    return render_template("index.html", active_page="home"), 404


@app.errorhandler(500)
def handle_500(_error):
    app.logger.error("Unhandled server error:\n%s", traceback.format_exc())
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "An unexpected server error occurred."}), 500
    return render_template("index.html", active_page="home"), 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
