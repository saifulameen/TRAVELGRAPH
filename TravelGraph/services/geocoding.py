"""
geocoding.py

Thin wrapper around the OpenStreetMap Nominatim search API, used to
power the location search boxes in the Directions panel.

This is used ONLY for search/autocomplete convenience — it plays no
role in the academic Dijkstra shortest-path calculation, which
operates purely on the predefined city graph in graph/graph_data.py.

If Nominatim is unreachable or slow, callers should treat an empty
list / None as "service unavailable" and fall back to the local
academic city list (see app.py).
"""

import requests

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
REQUEST_TIMEOUT_SECONDS = 4

# Nominatim's usage policy requires a descriptive User-Agent.
HEADERS = {
    "User-Agent": "TravelGraph-CollegeProject/1.0 (educational use)"
}


def search_locations(query, limit=5):
    """
    Search for place names matching `query` using Nominatim.

    Returns a list of dicts: [{"name": ..., "lat": ..., "lon": ...}, ...]
    Returns an empty list on any failure (network error, timeout,
    malformed response) rather than raising, so the caller can
    gracefully fall back.
    """
    if not query or not query.strip():
        return []

    params = {
        "q": query.strip(),
        "format": "jsonv2",
        "limit": limit,
        "countrycodes": "in",
    }

    try:
        response = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        results = response.json()
    except (requests.RequestException, ValueError):
        return []

    locations = []
    for item in results:
        try:
            locations.append({
                "name": item.get("display_name", "Unknown location"),
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
            })
        except (KeyError, ValueError, TypeError):
            continue

    return locations
