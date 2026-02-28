"""
Decisions API Routes — AI decision management.
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Query

from db.redis_manager import get_redis, RedisStateManager

router = APIRouter(prefix="/api/decisions", tags=["decisions"])


@router.get("/live")
async def get_live_decisions():
    """Get latest AI decisions."""
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        decisions = await rsm.get_last_decisions()
        return {"decisions": decisions or []}
    except Exception:
        return {"decisions": []}


@router.get("/history")
async def get_decision_history(page: int = Query(1, ge=1), per_page: int = Query(20, ge=1, le=100)):
    """Get paginated decision history from database."""
    try:
        from db.database import async_session_factory
        from models.decision import AIDecision
        from sqlalchemy import select, func

        async with async_session_factory() as session:
            # Count
            count_q = select(func.count()).select_from(AIDecision)
            total = (await session.execute(count_q)).scalar() or 0

            # Fetch page
            q = (
                select(AIDecision)
                .order_by(AIDecision.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
            )
            result = await session.execute(q)
            decisions = [d.to_dict() for d in result.scalars().all()]

        return {
            "decisions": decisions,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page,
        }
    except Exception as e:
        return {"decisions": [], "total": 0, "page": page, "error": str(e)}


@router.post("/{decision_id}/approve")
async def approve_decision(decision_id: str):
    """Approve an AI decision."""
    try:
        from db.database import async_session_factory
        from models.decision import AIDecision
        from sqlalchemy import select

        async with async_session_factory() as session:
            q = select(AIDecision).where(AIDecision.id == decision_id)
            result = await session.execute(q)
            decision = result.scalar_one_or_none()
            if decision:
                decision.approved_by = "operator"
                decision.executed_at = datetime.now(timezone.utc)
                await session.commit()
                return {"status": "approved", "decision_id": decision_id}
            return {"status": "not_found", "decision_id": decision_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/{decision_id}/reject")
async def reject_decision(decision_id: str):
    """Reject an AI decision."""
    return {"status": "rejected", "decision_id": decision_id}
