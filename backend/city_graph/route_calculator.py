"""
Route Calculator — shortest path and alternative routes on city graph.
"""

import logging
from typing import Optional

import networkx as nx

from city_graph.graph_builder import get_graph

logger = logging.getLogger(__name__)


def shortest_path(
    origin_id: str, destination_id: str, graph: Optional[nx.Graph] = None
) -> Optional[list[str]]:
    """Find the shortest path between two intersections."""
    G = graph or get_graph()
    if G is None:
        return None
    try:
        return nx.shortest_path(G, origin_id, destination_id, weight="weight")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None


def alternative_routes(
    origin_id: str, destination_id: str, k: int = 3, graph: Optional[nx.Graph] = None
) -> list[list[str]]:
    """Find k-shortest alternative routes."""
    G = graph or get_graph()
    if G is None:
        return []
    try:
        paths = list(nx.shortest_simple_paths(G, origin_id, destination_id, weight="weight"))
        return paths[:k]
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []


def get_affected_intersections(
    intersection_id: str, radius_hops: int = 2, graph: Optional[nx.Graph] = None
) -> list[str]:
    """Get all intersections within N hops of a given intersection."""
    G = graph or get_graph()
    if G is None:
        return []
    try:
        return list(nx.ego_graph(G, intersection_id, radius=radius_hops).nodes())
    except nx.NodeNotFound:
        return []
