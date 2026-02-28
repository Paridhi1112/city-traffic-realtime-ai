"""
Incident model — traffic incidents from HERE API and other sources.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from db.database import Base


class Incident(Base):
    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    intersection_id = Column(UUID(as_uuid=True), ForeignKey("intersections.id"), nullable=True)
    incident_type = Column(String, nullable=False)  # accident, road_work, closure, hazard
    severity = Column(Integer, default=1)  # 0=minor, 1=moderate, 2=major, 3=critical
    description = Column(Text, nullable=True)
    source = Column(String, default="here")  # here, tomtom, manual
    detected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "intersection_id": str(self.intersection_id) if self.intersection_id else None,
            "incident_type": self.incident_type,
            "severity": self.severity,
            "description": self.description,
            "source": self.source,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }
