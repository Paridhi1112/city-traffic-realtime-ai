"""
Congestion Model — XGBoost wrapper for T+15/30/60 prediction.
"""

import logging
import os
import pickle
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

MODEL_DIR = Path("/app/ml_models/trained")
MODEL_PATHS = {
    "15min": MODEL_DIR / "congestion_15min.pkl",
    "30min": MODEL_DIR / "congestion_30min.pkl",
    "60min": MODEL_DIR / "congestion_60min.pkl",
}

_models: dict = {}


def load_models():
    """Load trained XGBoost models from disk."""
    global _models
    for horizon, path in MODEL_PATHS.items():
        if path.exists():
            try:
                with open(path, "rb") as f:
                    _models[horizon] = pickle.load(f)
                logger.info(f"Loaded model for {horizon}: {path}")
            except Exception as e:
                logger.error(f"Failed to load model {path}: {e}")
        else:
            logger.warning(f"Model not found: {path} — predictions will use fallback")


def predict(features: np.ndarray, horizon: str = "15min") -> float:
    """Predict congestion for a given time horizon."""
    model = _models.get(horizon)
    if model is None:
        # Fallback: simple heuristic based on current congestion
        current = features[0, 5] if features.shape[1] > 5 else 30
        noise = np.random.uniform(-5, 10)
        multipliers = {"15min": 1.05, "30min": 1.1, "60min": 1.15}
        return float(np.clip(current * multipliers.get(horizon, 1.0) + noise, 0, 100))

    try:
        pred = model.predict(features)
        return float(np.clip(pred[0], 0, 100))
    except Exception as e:
        logger.error(f"Prediction failed for {horizon}: {e}")
        return float(features[0, 5]) if features.shape[1] > 5 else 30.0


def are_models_loaded() -> bool:
    return len(_models) > 0
