"""
Intersections API Routes.
"""

from fastapi import APIRouter
from db.redis_manager import get_redis, RedisStateManager

router = APIRouter(prefix="/api/intersections", tags=["intersections"])


@router.get("/")
async def list_intersections():
    """List all monitored intersections with current state."""
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        states = await rsm.get_all_intersection_states()
        return {"intersections": states, "count": len(states)}
    except Exception:
        return {"intersections": [], "count": 0}


@router.get("/{intersection_id}")
async def get_intersection_detail(intersection_id: str):
    """Get detailed info for one intersection."""
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        state = await rsm.get_intersection_state(intersection_id)
        prediction = await rsm.get_prediction(intersection_id)
        return {"state": state, "prediction": prediction}
    except Exception:
        return {"state": None, "prediction": None}
