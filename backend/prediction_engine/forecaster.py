"""
Forecaster — Runs XGBoost predictions on all intersections.
Stores results in Redis + DB.
"""

import logging
import uuid
from datetime import datetime, timezone

from prediction_engine.feature_builder import build_features_for_intersection
from prediction_engine.congestion_model import predict, load_models, are_models_loaded
from db.redis_manager import get_redis, RedisStateManager

logger = logging.getLogger(__name__)
_initialized = False


async def run_forecasts(intersections: list[dict]) -> list[dict]:
    """Run predictions for all intersections and store results."""
    global _initialized
    if not _initialized:
        load_models()
        _initialized = True

    # Get current data from Redis
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        weather = await rsm.get_weather()
    except Exception:
        weather = {}

    predictions = []
    for inter in intersections:
        # Get current state from Redis
        try:
            state = await rsm.get_intersection_state(inter["id"])
        except Exception:
            state = inter

        if not state:
            state = inter

        features = build_features_for_intersection(state, weather)

        pred_15 = predict(features, "15min")
        pred_30 = predict(features, "30min")
        pred_60 = predict(features, "60min")

        confidence = 0.85 if are_models_loaded() else 0.5

        prediction = {
            "intersection_id": inter["id"],
            "predicted_at": datetime.now(timezone.utc).isoformat(),
            "forecast_15min": round(pred_15, 1),
            "forecast_30min": round(pred_30, 1),
            "forecast_60min": round(pred_60, 1),
            "model_version": "v1.0" if are_models_loaded() else "heuristic",
            "confidence": confidence,
        }
        predictions.append(prediction)

        # Cache in Redis
        try:
            await rsm.set_prediction(inter["id"], prediction)
        except Exception:
            pass

    # Store in DB
    try:
        from db.database import async_session_factory
        from models.prediction import Prediction

        async with async_session_factory() as session:
            for pred in predictions:
                db_pred = Prediction(
                    id=uuid.uuid4(),
                    intersection_id=pred["intersection_id"],
                    forecast_15min=pred["forecast_15min"],
                    forecast_30min=pred["forecast_30min"],
                    forecast_60min=pred["forecast_60min"],
                    model_version=pred["model_version"],
                    confidence=pred["confidence"],
                )
                session.add(db_pred)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to store predictions in DB: {e}")

    logger.info(f"Generated {len(predictions)} predictions")
    return predictions
