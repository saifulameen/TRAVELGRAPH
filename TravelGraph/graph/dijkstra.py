"""
dijkstra.py

A manual implementation of Dijkstra's shortest-path algorithm using a
binary min-heap (Python's heapq module) as the priority queue.

No external shortest-path library (e.g. networkx) is used here. This
is the academic core of the TravelGraph project.

Algorithm outline:
    1. Initialize distances of all nodes to infinity, except the
       source which is 0.
    2. Push (0, source) onto a min-priority queue.
    3. Repeatedly pop the node with the smallest known distance.
    4. If it's already been finalized (visited), skip it.
    5. Otherwise mark it visited and relax all of its edges: for each
       neighbour, if going through the current node produces a
       shorter distance than previously known, update it and record
       the current node as the neighbour's predecessor ("previous").
    6. Push the updated (distance, neighbour) onto the heap.
    7. Continue until the heap is empty or the destination has been
       finalized.
    8. Reconstruct the shortest path by walking backwards through the
       "previous" pointers from the destination to the source.
"""

import heapq


def dijkstra_shortest_path(graph, source, destination):
    """
    Compute the shortest path between `source` and `destination` in a
    weighted adjacency-list graph using Dijkstra's algorithm.

    Args:
        graph: dict[str, dict[str, float]] adjacency list,
               e.g. {"Chennai": {"Vellore": 140, ...}, ...}
        source: name of the starting vertex
        destination: name of the target vertex

    Returns:
        A dict with:
            success (bool)
            path (list[str])            - vertices in order, empty if none
            distance (float | None)     - total shortest distance
            visited_nodes (list[str])   - order in which nodes were finalized
            algorithm_steps (list[dict])- step-by-step trace for the visualizer
    """
    if source not in graph or destination not in graph:
        return {
            "success": False,
            "path": [],
            "distance": None,
            "visited_nodes": [],
            "algorithm_steps": [],
            "error": "Source or destination not found in graph.",
        }

    # Step 1: initialize distances to infinity, source to 0.
    distances = {node: float("inf") for node in graph}
    distances[source] = 0

    # Predecessor map for path reconstruction.
    previous = {node: None for node in graph}

    # Track which nodes have been finalized (visited).
    visited = set()
    visited_order = []

    # Step-by-step trace, used by the front-end Dijkstra Visualizer.
    algorithm_steps = []

    # Step 2: min-priority queue of (distance, node), seeded with source.
    priority_queue = [(0, source)]

    step_number = 0

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        # Skip stale entries (a shorter distance was already found).
        if current_node in visited:
            continue

        # Step 4/5: finalize this node.
        visited.add(current_node)
        visited_order.append(current_node)
        step_number += 1

        # Snapshot of the priority queue contents (deduplicated, sorted)
        # at this point in time, for the visualizer.
        pq_snapshot = sorted(
            [(node, dist) for dist, node in priority_queue if node not in visited],
            key=lambda x: x[1],
        )

        algorithm_steps.append({
            "step": step_number,
            "current_node": current_node,
            "current_distance": current_distance,
            "visited_so_far": list(visited_order),
            "priority_queue_snapshot": [
                {"node": n, "distance": d} for n, d in pq_snapshot
            ],
            "relaxed_edges": [],
        })

        # Early exit once the destination has been finalized.
        if current_node == destination:
            break

        # Step 6: relax edges to all neighbours.
        relaxed_this_step = []
        for neighbour, weight in graph[current_node].items():
            if neighbour in visited:
                continue

            candidate_distance = current_distance + weight

            if candidate_distance < distances[neighbour]:
                distances[neighbour] = candidate_distance
                previous[neighbour] = current_node
                heapq.heappush(priority_queue, (candidate_distance, neighbour))
                relaxed_this_step.append({
                    "neighbour": neighbour,
                    "new_distance": candidate_distance,
                    "via": current_node,
                })

        algorithm_steps[-1]["relaxed_edges"] = relaxed_this_step

    # Step 8: reconstruct path by walking backwards from destination.
    if distances[destination] == float("inf"):
        return {
            "success": False,
            "path": [],
            "distance": None,
            "visited_nodes": visited_order,
            "algorithm_steps": algorithm_steps,
            "error": "No path exists between the selected cities.",
        }

    path = []
    node = destination
    while node is not None:
        path.append(node)
        node = previous[node]
    path.reverse()

    return {
        "success": True,
        "path": path,
        "distance": distances[destination],
        "visited_nodes": visited_order,
        "algorithm_steps": algorithm_steps,
        "error": None,
    }
