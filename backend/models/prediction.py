"""
Prediction model — stores XGBoost congestion forecasts.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from db.database import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intersection_id = Column(UUID(as_uuid=True), ForeignKey("intersections.id"), nullable=False)
    predicted_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    forecast_15min = Column(Float, default=0.0)
    forecast_30min = Column(Float, default=0.0)
    forecast_60min = Column(Float, default=0.0)
    model_version = Column(String, default="v1.0")
    confidence = Column(Float, default=0.0)

    def to_dict(self):
        return {
            "id": str(self.id),
            "intersection_id": str(self.intersection_id),
            "predicted_at": self.predicted_at.isoformat() if self.predicted_at else None,
            "forecast_15min": self.forecast_15min,
            "forecast_30min": self.forecast_30min,
            "forecast_60min": self.forecast_60min,
            "model_version": self.model_version,
            "confidence": self.confidence,
        }
