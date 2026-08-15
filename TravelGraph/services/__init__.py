"""
services package

Contains integrations with external geographic services:
    - geocoding.py: Nominatim (OpenStreetMap) location search
    - routing.py:   OSRM road-geometry lookups

Both services are optional/best-effort. If either is unavailable, the
application falls back gracefully (see app.py) and the core Dijkstra
route calculation still works using the academic graph.
"""
