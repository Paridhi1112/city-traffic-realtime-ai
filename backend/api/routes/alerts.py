"""
Alerts API Routes.
"""

from datetime import datetime, timezone
from fastapi import APIRouter
from db.redis_manager import get_redis, RedisStateManager

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("/active")
async def get_active_alerts():
    """Get active unresolved alerts."""
    try:
        from db.database import async_session_factory
        from models.alert import Alert
        from sqlalchemy import select

        async with async_session_factory() as session:
            q = (
                select(Alert)
                .where(Alert.resolved_at.is_(None))
                .order_by(Alert.detected_at.desc())
                .limit(50)
            )
            result = await session.execute(q)
            alerts = [a.to_dict() for a in result.scalars().all()]
        return {"alerts": alerts}
    except Exception:
        return {"alerts": []}


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """Acknowledge an alert."""
    try:
        from db.database import async_session_factory
        from models.alert import Alert
        from sqlalchemy import select

        async with async_session_factory() as session:
            q = select(Alert).where(Alert.id == alert_id)
            result = await session.execute(q)
            alert = result.scalar_one_or_none()
            if alert:
                alert.acknowledged_by = "operator"
                alert.resolved_at = datetime.now(timezone.utc)
                await session.commit()
                return {"status": "acknowledged", "alert_id": alert_id}
        return {"status": "not_found"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
