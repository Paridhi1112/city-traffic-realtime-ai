"""
TrafficState model — time-series traffic data per intersection.
This table becomes a TimescaleDB hypertable partitioned on timestamp.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from db.database import Base


class TrafficState(Base):
    __tablename__ = "traffic_states"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intersection_id = Column(UUID(as_uuid=True), ForeignKey("intersections.id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    congestion_percent = Column(Float, default=0.0)
    jam_factor = Column(Float, default=0.0)
    current_speed_kmh = Column(Float, default=0.0)
    freeflow_speed_kmh = Column(Float, default=0.0)
    weather_impact_factor = Column(Float, default=1.0)
    data_source = Column(String, default="aggregated")

    def to_dict(self):
        return {
            "id": str(self.id),
            "intersection_id": str(self.intersection_id),
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "congestion_percent": self.congestion_percent,
            "jam_factor": self.jam_factor,
            "current_speed_kmh": self.current_speed_kmh,
            "freeflow_speed_kmh": self.freeflow_speed_kmh,
            "weather_impact_factor": self.weather_impact_factor,
            "data_source": self.data_source,
        }
