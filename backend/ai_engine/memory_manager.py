"""
Memory Manager — Tracks last N decisions for prompt continuity.
"""

import logging
from typing import Optional

from db.redis_manager import RedisStateManager

logger = logging.getLogger(__name__)


async def get_recent_decisions(rsm: RedisStateManager, limit: int = 3) -> list[dict]:
    """Get the last N decisions from Redis for prompt context."""
    try:
        decisions = await rsm.get_last_decisions()
        if decisions:
            return decisions[:limit]
    except Exception as e:
        logger.warning(f"Failed to get recent decisions: {e}")
    return []


async def store_decisions(rsm: RedisStateManager, decisions: list[dict]):
    """Store decisions in Redis for future context."""
    try:
        await rsm.set_last_decisions(decisions)
    except Exception as e:
        logger.error(f"Failed to store decisions: {e}")
