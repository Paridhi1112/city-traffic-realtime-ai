"""
GTFS Fetcher — Public transit data stub.
Returns simulated bus positions and delays in simulation mode.
Full GTFS integration would parse feeds from transitfeeds.com.
"""

import logging
import random
from datetime import datetime, timezone

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _simulate_transit_data(intersections: list[dict]) -> dict:
    """Generate simulated public transit data."""
    bus_positions = []
    delays = []

    # Simulate 5-15 buses near intersections
    count = random.randint(5, 15)
    sample = random.sample(intersections, min(count, len(intersections)))

    for inter in sample:
        bus_positions.append({
            "vehicle_id": f"BUS-{random.randint(100, 999)}",
            "route": f"Route {random.choice(['1', '3', '7', '11', '21', '34', '42', '65', '83', '101'])}",
            "lat": inter["lat"] + random.uniform(-0.005, 0.005),
            "lng": inter["lng"] + random.uniform(-0.005, 0.005),
            "speed_kmh": random.uniform(5, 35),
            "delay_minutes": max(0, random.gauss(5, 8)),
            "near_intersection_id": inter["id"],
        })

        if random.random() < 0.3:  # 30% chance of delay
            delays.append({
                "intersection_id": inter["id"],
                "delay_minutes": round(random.uniform(2, 20), 1),
                "cause": random.choice(["bus_stop_congestion", "passenger_loading", "signal_wait", "traffic_jam"]),
            })

    return {
        "bus_positions": bus_positions,
        "delays": delays,
        "total_active_buses": len(bus_positions),
        "average_delay_minutes": round(
            sum(d["delay_minutes"] for d in delays) / max(len(delays), 1), 1
        ),
        "source": "gtfs_simulated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def fetch_transit_data(intersections: list[dict]) -> dict:
    """Fetch public transit data. Currently simulation-only."""
    # Full GTFS integration would:
    # 1. Download GTFS-realtime feed from transitfeeds.com
    # 2. Parse protobuf vehicle positions
    # 3. Map to nearest intersections
    # For now, return simulated data
    return _simulate_transit_data(intersections)
