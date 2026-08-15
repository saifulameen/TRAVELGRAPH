"""
routing.py

Thin wrapper around the public OSRM (Open Source Routing Machine) API,
used ONLY to obtain realistic road geometry for display on the map.

IMPORTANT ACADEMIC DISTINCTION:
    - Dijkstra (graph/dijkstra.py) determines WHICH cities the route
      passes through (the shortest path through the academic graph).
    - OSRM is called separately for EACH consecutive city-pair segment
      in that Dijkstra path, purely to get a road-following polyline
      and a real-world duration estimate for drawing on the map.

OSRM is never asked to compute source-to-destination directly for the
whole trip; it only ever sees one graph edge (one segment) at a time,
so it cannot silently replace the Dijkstra result.
"""

import requests

OSRM_BASE_URL = "https://router.project-osrm.org/route/v1/driving"
REQUEST_TIMEOUT_SECONDS = 5


def get_route_geometry(start_coords, end_coords):
    """
    Fetch road geometry for a single segment between two points.

    Args:
        start_coords: {"lat": float, "lon": float}
        end_coords:   {"lat": float, "lon": float}

    Returns a dict:
        {
            "success": bool,
            "geometry": [[lat, lon], [lat, lon], ...],  # empty if failed
            "distance_meters": float | None,
            "duration_seconds": float | None,
        }

    Never raises — on any failure returns success: False so the caller
    can fall back to a straight line between the two cities.
    """
    coordinates = (
        f"{start_coords['lon']},{start_coords['lat']};"
        f"{end_coords['lon']},{end_coords['lat']}"
    )
    url = f"{OSRM_BASE_URL}/{coordinates}"
    params = {"overview": "full", "geometries": "geojson"}

    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()

        if data.get("code") != "Ok" or not data.get("routes"):
            return {
                "success": False,
                "geometry": [],
                "distance_meters": None,
                "duration_seconds": None,
            }

        route = data["routes"][0]
        raw_coords = route["geometry"]["coordinates"]  # [[lon, lat], ...]

        # Leaflet expects [lat, lon] pairs.
        geometry = [[lat, lon] for lon, lat in raw_coords]

        return {
            "success": True,
            "geometry": geometry,
            "distance_meters": route.get("distance"),
            "duration_seconds": route.get("duration"),
        }

    except (requests.RequestException, ValueError, KeyError, IndexError):
        return {
            "success": False,
            "geometry": [],
            "distance_meters": None,
            "duration_seconds": None,
        }


def get_multi_segment_geometry(city_path, coordinates_lookup):
    """
    Given an ordered list of city names (the Dijkstra path) and a
    lookup dict of {city_name: {"lat":..., "lon":...}}, fetch OSRM
    road geometry for each consecutive pair and combine them into one
    continuous route.

    Returns:
        {
            "success": bool,           # True if at least one segment succeeded
            "all_segments_ok": bool,   # True only if every segment succeeded
            "combined_geometry": [[lat, lon], ...],
            "segments": [
                {
                    "from": str, "to": str,
                    "success": bool,
                    "geometry": [[lat, lon], ...],
                    "distance_meters": float | None,
                    "duration_seconds": float | None,
                },
                ...
            ],
        }
    """
    segments = []
    combined_geometry = []
    any_success = False
    all_ok = True

    for i in range(len(city_path) - 1):
        city_a = city_path[i]
        city_b = city_path[i + 1]

        start = coordinates_lookup.get(city_a)
        end = coordinates_lookup.get(city_b)

        if not start or not end:
            segments.append({
                "from": city_a, "to": city_b, "success": False,
                "geometry": [], "distance_meters": None, "duration_seconds": None,
            })
            all_ok = False
            continue

        result = get_route_geometry(start, end)

        if result["success"]:
            any_success = True
            combined_geometry.extend(result["geometry"])
        else:
            all_ok = False
            # Fallback: straight line between the two city points so the
            # map still shows *something* for this segment.
            combined_geometry.extend([
                [start["lat"], start["lon"]],
                [end["lat"], end["lon"]],
            ])

        segments.append({
            "from": city_a,
            "to": city_b,
            "success": result["success"],
            "geometry": result["geometry"],
            "distance_meters": result["distance_meters"],
            "duration_seconds": result["duration_seconds"],
        })

    return {
        "success": any_success,
        "all_segments_ok": all_ok,
        "combined_geometry": combined_geometry,
        "segments": segments,
    }
