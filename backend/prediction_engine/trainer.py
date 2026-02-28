"""
Trainer — XGBoost training pipeline.
Loads CSV → feature engineering → trains models → saves to disk.
"""

import logging
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import xgboost as xgb

from prediction_engine.feature_builder import FEATURE_COLUMNS

logger = logging.getLogger(__name__)

MODEL_DIR = Path("/app/ml_models/trained")
DATA_DIR = Path("/app/ml_models/datasets")


def train_model(target_column: str, model_name: str) -> dict:
    """Train XGBoost model for a specific forecast horizon."""
    csv_path = DATA_DIR / "sample_training_data.csv"
    if not csv_path.exists():
        logger.error(f"Training data not found: {csv_path}")
        return {"error": "No training data"}

    df = pd.read_csv(csv_path)

    # Validate columns
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        logger.error(f"Missing columns in training data: {missing}")
        return {"error": f"Missing columns: {missing}"}

    if target_column not in df.columns:
        logger.error(f"Target column {target_column} not in data")
        return {"error": f"Missing target: {target_column}"}

    X = df[FEATURE_COLUMNS].values
    y = df[target_column].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = xgb.XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective="reg:squarederror",
        random_state=42,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Save model
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / f"{model_name}.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)

    logger.info(f"Trained {model_name}: MAE={mae:.2f}, R²={r2:.3f}")
    return {
        "model_name": model_name,
        "mae": round(mae, 2),
        "r2": round(r2, 3),
        "model_path": str(model_path),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
    }


def train_all_models() -> list[dict]:
    """Train models for all three forecast horizons."""
    results = []
    targets = [
        ("congestion_15min", "congestion_15min"),
        ("congestion_30min", "congestion_30min"),
        ("congestion_60min", "congestion_60min"),
    ]

    for target_col, model_name in targets:
        result = train_model(target_col, model_name)
        results.append(result)

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    results = train_all_models()
    for r in results:
        print(r)
