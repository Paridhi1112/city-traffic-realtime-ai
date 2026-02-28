"""
CityEvent model — concerts, sports, holidays, etc. that affect traffic.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from db.database import Base


class CityEvent(Base):
    __tablename__ = "city_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    source = Column(String, default="manual")  # ticketmaster, eventbrite, holiday_api, manual
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    radius_meters = Column(Integer, default=2000)
    expected_attendance = Column(Integer, default=0)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    impact_loaded = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "source": self.source,
            "lat": self.lat,
            "lng": self.lng,
            "radius_meters": self.radius_meters,
            "expected_attendance": self.expected_attendance,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "impact_loaded": self.impact_loaded,
        }
