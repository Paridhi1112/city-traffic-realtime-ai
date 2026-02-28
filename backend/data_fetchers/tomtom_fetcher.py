"""
TomTom Fetcher — Fetches real-time traffic flow data from TomTom API.
In simulation mode, generates realistic traffic flow data.
"""

import logging
import random
from datetime import datetime, timezone
from typing import Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TOMTOM_FLOW_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"


def _simulate_traffic_flow(intersection: dict) -> dict:
    """Generate realistic simulated traffic flow for one intersection."""
    hour = datetime.now().hour
    # Peak hours = more congestion
    if 8 <= hour <= 10 or 17 <= hour <= 20:
        base_congestion = random.uniform(40, 85)
    elif 11 <= hour <= 16:
        base_congestion = random.uniform(20, 55)
    else:
        base_congestion = random.uniform(5, 30)

    freeflow = random.uniform(40, 80)
    current_speed = freeflow * (1 - base_congestion / 100)

    return {
        "intersection_id": intersection["id"],
        "current_speed_kmh": round(max(current_speed, 5), 1),
        "freeflow_speed_kmh": round(freeflow, 1),
        "congestion_percent": round(base_congestion, 1),
        "confidence": round(random.uniform(0.7, 1.0), 2),
        "current_travel_time": round(random.uniform(30, 300)),
        "freeflow_travel_time": round(random.uniform(20, 120)),
        "source": "tomtom_simulated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def fetch_traffic_flow(intersections: list[dict]) -> list[dict]:
    """Fetch TomTom traffic flow for all intersections.
    Batches to stay within 2500/day free tier.
    """
    if settings.simulation_mode or not settings.tomtom_api_key:
        logger.info(f"Simulation mode — generating traffic for {len(intersections)} intersections")
        return [_simulate_traffic_flow(i) for i in intersections]

    results = []
    # Sample subset if too many intersections (API rate limit)
    sample = intersections[:25]  # Max 25 per poll cycle to conserve quota

    async with httpx.AsyncClient(timeout=30) as client:
        for inter in sample:
            try:
                resp = await client.get(
                    TOMTOM_FLOW_URL,
                    params={
                        "key": settings.tomtom_api_key,
                        "point": f"{inter['lat']},{inter['lng']}",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                flow = data.get("flowSegmentData", {})

                freeflow = flow.get("freeFlowSpeed", 50)
                current = flow.get("currentSpeed", 50)
                congestion = max(0, (1 - current / max(freeflow, 1)) * 100)

                results.append({
                    "intersection_id": inter["id"],
                    "current_speed_kmh": round(current, 1),
                    "freeflow_speed_kmh": round(freeflow, 1),
                    "congestion_percent": round(congestion, 1),
                    "confidence": flow.get("confidence", 0.5),
                    "current_travel_time": flow.get("currentTravelTime", 0),
                    "freeflow_travel_time": flow.get("freeFlowTravelTime", 0),
                    "source": "tomtom",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as e:
                logger.warning(f"TomTom fetch failed for {inter['id']}: {e}")
                results.append(_simulate_traffic_flow(inter))

    # Fill remaining intersections with simulated data
    fetched_ids = {r["intersection_id"] for r in results}
    for inter in intersections:
        if inter["id"] not in fetched_ids:
            results.append(_simulate_traffic_flow(inter))

    return results
