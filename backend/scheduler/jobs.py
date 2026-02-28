"""
Scheduled Job Definitions — called by APScheduler.
"""

import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# WebSocket broadcast callback (set during app startup)
_ws_broadcast = None


def set_ws_broadcast(callback):
    global _ws_broadcast
    _ws_broadcast = callback


async def job_fetch_all_data(intersections: list[dict]):
    """STEP 1-2: Fetch data from all sources and aggregate."""
    try:
        from data_fetchers.data_aggregator import aggregate_all_data

        city_state = await aggregate_all_data(intersections)

        # Broadcast to WebSocket clients
        if _ws_broadcast:
            await _ws_broadcast({
                "type": "city_state_update",
                "data": city_state,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        logger.info(f"Data fetch complete — avg congestion: {city_state.get('average_congestion_percent', 0):.1f}%")
    except Exception as e:
        logger.error(f"Data fetch job failed: {e}", exc_info=True)


async def job_run_predictions(intersections: list[dict]):
    """STEP 3: Run XGBoost predictions."""
    try:
        from prediction_engine.forecaster import run_forecasts

        predictions = await run_forecasts(intersections)

        if _ws_broadcast:
            await _ws_broadcast({
                "type": "predictions_update",
                "data": predictions,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        logger.info(f"Predictions complete — {len(predictions)} forecasts generated")
    except Exception as e:
        logger.error(f"Prediction job failed: {e}", exc_info=True)


async def job_run_ai_decisions(intersections: list[dict]):
    """STEP 4: Run Kimi AI decision loop."""
    try:
        from ai_engine.kimi_client import get_ai_decisions

        decisions = await get_ai_decisions(intersections)

        if _ws_broadcast and decisions:
            await _ws_broadcast({
                "type": "ai_decisions_update",
                "data": decisions,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        logger.info(f"AI decisions complete — {len(decisions.get('decisions', []))} decisions made")
    except Exception as e:
        logger.error(f"AI decision job failed: {e}", exc_info=True)


async def job_flush_to_db():
    """Flush current state from Redis to TimescaleDB."""
    try:
        from db.redis_manager import get_redis, RedisStateManager
        from data_fetchers.data_aggregator import write_to_timescaledb

        r = await get_redis()
        rsm = RedisStateManager(r)
        city_state = await rsm.get_city_state()
        if city_state:
            await write_to_timescaledb(city_state)
            logger.info("Flushed state to TimescaleDB")
    except Exception as e:
        logger.error(f"DB flush job failed: {e}", exc_info=True)
