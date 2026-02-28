"""
Events API Routes.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone
from db.redis_manager import get_redis, RedisStateManager

router = APIRouter(prefix="/api/events", tags=["events"])


class EventCreate(BaseModel):
    name: str
    lat: float
    lng: float
    radius_meters: int = 2000
    expected_attendance: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None


@router.get("/active")
async def get_active_events():
    """Get currently active events."""
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        events = await rsm.get_events()
        return {"events": events or []}
    except Exception:
        return {"events": []}


@router.post("/")
async def create_event(event: EventCreate):
    """Manually create a city event."""
    try:
        from db.database import async_session_factory
        from models.event import CityEvent
        import uuid

        async with async_session_factory() as session:
            db_event = CityEvent(
                id=uuid.uuid4(),
                name=event.name,
                source="manual",
                lat=event.lat,
                lng=event.lng,
                radius_meters=event.radius_meters,
                expected_attendance=event.expected_attendance,
            )
            session.add(db_event)
            await session.commit()
            return {"status": "created", "event": db_event.to_dict()}
    except Exception as e:
        return {"status": "error", "error": str(e)}
