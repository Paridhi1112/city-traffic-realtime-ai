"""
Redis State Manager — caches live city traffic state.
"""

import json
import logging
from typing import Optional
from datetime import datetime, timezone
import redis.asyncio as redis
from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


class RedisStateManager:
    """Manages traffic state in Redis with JSON serialization."""

    CITY_STATE_KEY = "city:state"
    INTERSECTION_PREFIX = "intersection:"
    WEATHER_KEY = "city:weather"
    EVENTS_KEY = "city:events"
    PREDICTIONS_PREFIX = "prediction:"
    DATASOURCE_STATUS_KEY = "datasources:status"
    LAST_DECISIONS_KEY = "city:last_decisions"
    TTL = 90  # seconds

    def __init__(self, client: redis.Redis):
        self.r = client

    # ── City State ──
    async def set_city_state(self, state: dict):
        state["_updated_at"] = datetime.now(timezone.utc).isoformat()
        await self.r.setex(self.CITY_STATE_KEY, self.TTL, json.dumps(state, default=str))

    async def get_city_state(self) -> Optional[dict]:
        raw = await self.r.get(self.CITY_STATE_KEY)
        return json.loads(raw) if raw else None

    # ── Per-Intersection ──
    async def set_intersection_state(self, intersection_id: str, state: dict):
        key = f"{self.INTERSECTION_PREFIX}{intersection_id}"
        await self.r.setex(key, self.TTL, json.dumps(state, default=str))

    async def get_intersection_state(self, intersection_id: str) -> Optional[dict]:
        raw = await self.r.get(f"{self.INTERSECTION_PREFIX}{intersection_id}")
        return json.loads(raw) if raw else None

    async def get_all_intersection_states(self) -> list[dict]:
        keys = []
        async for key in self.r.scan_iter(f"{self.INTERSECTION_PREFIX}*"):
            keys.append(key)
        if not keys:
            return []
        values = await self.r.mget(keys)
        return [json.loads(v) for v in values if v]

    # ── Weather ──
    async def set_weather(self, weather: dict):
        await self.r.setex(self.WEATHER_KEY, 300, json.dumps(weather, default=str))

    async def get_weather(self) -> Optional[dict]:
        raw = await self.r.get(self.WEATHER_KEY)
        return json.loads(raw) if raw else None

    # ── Events ──
    async def set_events(self, events: list[dict]):
        await self.r.setex(self.EVENTS_KEY, 600, json.dumps(events, default=str))

    async def get_events(self) -> Optional[list[dict]]:
        raw = await self.r.get(self.EVENTS_KEY)
        return json.loads(raw) if raw else None

    # ── Predictions ──
    async def set_prediction(self, intersection_id: str, prediction: dict):
        key = f"{self.PREDICTIONS_PREFIX}{intersection_id}"
        await self.r.setex(key, 600, json.dumps(prediction, default=str))

    async def get_prediction(self, intersection_id: str) -> Optional[dict]:
        raw = await self.r.get(f"{self.PREDICTIONS_PREFIX}{intersection_id}")
        return json.loads(raw) if raw else None

    # ── Datasource Status ──
    async def set_datasource_status(self, status: dict):
        await self.r.set(self.DATASOURCE_STATUS_KEY, json.dumps(status, default=str))

    async def get_datasource_status(self) -> Optional[dict]:
        raw = await self.r.get(self.DATASOURCE_STATUS_KEY)
        return json.loads(raw) if raw else None

    # ── Last AI Decisions ──
    async def set_last_decisions(self, decisions: list[dict]):
        await self.r.setex(self.LAST_DECISIONS_KEY, 300, json.dumps(decisions, default=str))

    async def get_last_decisions(self) -> Optional[list[dict]]:
        raw = await self.r.get(self.LAST_DECISIONS_KEY)
        return json.loads(raw) if raw else None
