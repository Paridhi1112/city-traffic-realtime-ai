"""
Alert model — system-generated traffic alerts.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from db.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intersection_id = Column(UUID(as_uuid=True), ForeignKey("intersections.id"), nullable=True)
    alert_type = Column(String, nullable=False)  # congestion, incident, weather, event
    severity = Column(String, default="info")  # info, warning, critical
    message = Column(Text, nullable=False)
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    acknowledged_by = Column(String, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "intersection_id": str(self.intersection_id) if self.intersection_id else None,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "acknowledged_by": self.acknowledged_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
