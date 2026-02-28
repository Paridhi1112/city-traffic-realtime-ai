"""
Graph Builder — constructs a NetworkX road graph from OSM data.
"""

import logging
from typing import Optional

import networkx as nx

logger = logging.getLogger(__name__)

_city_graph: Optional[nx.Graph] = None


def build_graph(intersections: list[dict]) -> nx.Graph:
    """Build a road graph from intersection list.
    Edges connect nearby intersections (within ~2km) to form a road network.
    """
    global _city_graph

    G = nx.Graph()

    for inter in intersections:
        G.add_node(
            inter["id"],
            lat=inter["lat"],
            lng=inter["lng"],
            name=inter.get("name", ""),
            zone=inter.get("zone", "general"),
        )

    # Connect intersections that are within ~2km of each other
    from math import radians, sin, cos, sqrt, atan2

    def haversine(lat1, lng1, lat2, lng2):
        R = 6371  # km
        dlat = radians(lat2 - lat1)
        dlng = radians(lng2 - lng1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
        return R * 2 * atan2(sqrt(a), sqrt(1 - a))

    for i, a in enumerate(intersections):
        for b in intersections[i + 1:]:
            dist = haversine(a["lat"], a["lng"], b["lat"], b["lng"])
            if dist < 2.0:  # 2km threshold
                G.add_edge(
                    a["id"], b["id"],
                    weight=dist,
                    distance_km=round(dist, 3),
                )

    _city_graph = G
    logger.info(f"Built city graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def get_graph() -> Optional[nx.Graph]:
    return _city_graph
