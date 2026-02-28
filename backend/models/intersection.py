"""
Intersection model — represents a monitored traffic intersection.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, BigInteger, ARRAY, DateTime
from sqlalchemy.dialects.postgresql import UUID
from db.database import Base


class Intersection(Base):
    __tablename__ = "intersections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    road_names = Column(ARRAY(String), default=[])
    num_lanes = Column(Integer, default=2)
    speed_limit_kmh = Column(Integer, default=50)
    zone = Column(String, default="general")
    osm_node_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "lat": self.lat,
            "lng": self.lng,
            "road_names": self.road_names or [],
            "num_lanes": self.num_lanes,
            "speed_limit_kmh": self.speed_limit_kmh,
            "zone": self.zone,
            "osm_node_id": self.osm_node_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
