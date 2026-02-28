"""
Traffic API Routes — city state, heatmap, intersection details.
"""

from fastapi import APIRouter, Query
from datetime import datetime, timezone

from db.redis_manager import get_redis, RedisStateManager

router = APIRouter(prefix="/api/traffic", tags=["traffic"])


@router.get("/city-state")
async def get_city_state():
    """Get full current city traffic state."""
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        state = await rsm.get_city_state()
        if state:
            return state
    except Exception:
        pass
    return {
        "city_name": "Not loaded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_intersections": 0,
        "average_congestion_percent": 0,
        "intersections": [],
        "weather": {},
        "active_events": [],
    }


@router.get("/intersection/{intersection_id}")
async def get_intersection(intersection_id: str):
    """Get traffic state for a specific intersection."""
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        state = await rsm.get_intersection_state(intersection_id)
        prediction = await rsm.get_prediction(intersection_id)
        return {
            "state": state,
            "prediction": prediction,
        }
    except Exception:
        return {"state": None, "prediction": None}


@router.get("/heatmap")
async def get_heatmap():
    """Return GeoJSON for Mapbox heatmap layer."""
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        states = await rsm.get_all_intersection_states()
    except Exception:
        states = []

    features = []
    for s in states:
        features.append({
            "type": "Feature",
            "properties": {
                "congestion": s.get("congestion_percent", 0),
                "jam_factor": s.get("jam_factor", 0),
                "speed": s.get("current_speed_kmh", 0),
                "intersection_id": s.get("intersection_id", ""),
                "road_names": s.get("road_names", []),
            },
            "geometry": {
                "type": "Point",
                "coordinates": [s.get("lng", 0), s.get("lat", 0)],
            },
        })

    return {
        "type": "FeatureCollection",
        "features": features,
    }
