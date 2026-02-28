"""
HERE Fetcher — Traffic flow + incidents from HERE Maps API.
Uses city-wide bbox query (single call) instead of per-point.
"""

import logging
import random
from datetime import datetime, timezone
from typing import Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

HERE_FLOW_URL = "https://data.traffic.hereapi.com/v7/flow"
HERE_INCIDENTS_URL = "https://data.traffic.hereapi.com/v7/incidents"


def _simulate_jam_factors(intersections: list[dict]) -> list[dict]:
    """Generate simulated jam factors (0-10 scale)."""
    hour = datetime.now().hour
    results = []
    for inter in intersections:
        if 8 <= hour <= 10 or 17 <= hour <= 20:
            jam = random.uniform(3, 9)
        elif 11 <= hour <= 16:
            jam = random.uniform(1, 6)
        else:
            jam = random.uniform(0, 3)
        results.append({
            "intersection_id": inter["id"],
            "jam_factor": round(jam, 1),
            "source": "here_simulated",
        })
    return results


def _simulate_incidents(intersections: list[dict]) -> list[dict]:
    """Generate simulated traffic incidents."""
    incident_types = ["accident", "road_work", "closure", "hazard"]
    descriptions = [
        "Minor fender bender, one lane blocked",
        "Road construction work in progress",
        "Water logging reported on road",
        "Pothole causing traffic slowdown",
        "VIP movement — road partially blocked",
        "Festival procession blocking road",
        "Fallen tree blocking lane",
        "Signal malfunction at junction",
    ]
    incidents = []
    # Only generate 0-3 incidents randomly
    count = random.randint(0, 3)
    if count > 0 and intersections:
        affected = random.sample(intersections, min(count, len(intersections)))
        for inter in affected:
            incidents.append({
                "intersection_id": inter["id"],
                "incident_type": random.choice(incident_types),
                "severity": random.randint(0, 3),
                "description": random.choice(descriptions),
                "source": "here_simulated",
                "lat": inter["lat"],
                "lng": inter["lng"],
                "detected_at": datetime.now(timezone.utc).isoformat(),
            })
    return incidents


async def fetch_here_flow(intersections: list[dict]) -> list[dict]:
    """Fetch HERE traffic flow for city bbox — single API call."""
    if settings.simulation_mode or not settings.here_api_key:
        return _simulate_jam_factors(intersections)

    s, w, n, e = settings.city_bbox_tuple
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                HERE_FLOW_URL,
                params={
                    "apiKey": settings.here_api_key,
                    "in": f"bbox:{w},{s},{e},{n}",
                    "locationReferencing": "shape",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        results = []
        for result in data.get("results", []):
            flow = result.get("currentFlow", {})
            jam = flow.get("jamFactor", 0)
            # Map to nearest intersection by location
            loc = result.get("location", {})
            shape = loc.get("shape", {}).get("links", [{}])
            if shape:
                points = shape[0].get("points", [])
                if points:
                    mid = points[len(points) // 2]
                    nearest = _find_nearest_intersection(
                        mid.get("lat", 0), mid.get("lng", 0), intersections
                    )
                    if nearest:
                        results.append({
                            "intersection_id": nearest["id"],
                            "jam_factor": round(jam, 1),
                            "source": "here",
                        })

        # Fill missing
        fetched_ids = {r["intersection_id"] for r in results}
        for inter in intersections:
            if inter["id"] not in fetched_ids:
                results.append({
                    "intersection_id": inter["id"],
                    "jam_factor": round(random.uniform(0, 5), 1),
                    "source": "here_estimated",
                })

        return results

    except Exception as e:
        logger.error(f"HERE flow fetch failed: {e}")
        return _simulate_jam_factors(intersections)


async def fetch_here_incidents(intersections: list[dict]) -> list[dict]:
    """Fetch HERE traffic incidents for city bbox."""
    if settings.simulation_mode or not settings.here_api_key:
        return _simulate_incidents(intersections)

    s, w, n, e = settings.city_bbox_tuple
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                HERE_INCIDENTS_URL,
                params={
                    "apiKey": settings.here_api_key,
                    "in": f"bbox:{w},{s},{e},{n}",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        incidents = []
        for result in data.get("results", []):
            inc = result.get("incidentDetails", {})
            loc = result.get("location", {})
            desc = inc.get("description", {}).get("value", "Traffic incident")

            incidents.append({
                "intersection_id": None,  # Will be mapped by aggregator
                "incident_type": inc.get("type", "unknown"),
                "severity": min(inc.get("criticality", 1), 3),
                "description": desc,
                "source": "here",
                "lat": loc.get("referencePoint", {}).get("lat", 0),
                "lng": loc.get("referencePoint", {}).get("lng", 0),
                "detected_at": datetime.now(timezone.utc).isoformat(),
            })
        return incidents

    except Exception as e:
        logger.error(f"HERE incidents fetch failed: {e}")
        return _simulate_incidents(intersections)


def _find_nearest_intersection(
    lat: float, lng: float, intersections: list[dict], max_dist_km: float = 2.0
) -> Optional[dict]:
    """Find the nearest intersection to a given point."""
    from math import radians, sin, cos, sqrt, atan2

    best = None
    best_dist = max_dist_km

    for inter in intersections:
        R = 6371
        dlat = radians(inter["lat"] - lat)
        dlng = radians(inter["lng"] - lng)
        a = sin(dlat / 2) ** 2 + cos(radians(lat)) * cos(radians(inter["lat"])) * sin(dlng / 2) ** 2
        d = R * 2 * atan2(sqrt(a), sqrt(1 - a))
        if d < best_dist:
            best_dist = d
            best = inter

    return best
