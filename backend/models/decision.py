"""
AIDecision model — stores Kimi AI traffic management decisions.
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from db.database import Base


class AIDecision(Base):
    __tablename__ = "ai_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    affected_intersections = Column(ARRAY(UUID(as_uuid=True)), default=[])
    decision_type = Column(String, nullable=False)  # signal_adjustment, reroute_suggestion, alert, preemptive_action
    action = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    expected_outcome = Column(Text, nullable=True)
    emission_impact = Column(String, nullable=True)
    confidence = Column(Integer, default=50)
    requires_approval = Column(Boolean, default=True)
    approved_by = Column(String, nullable=True)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    urgency = Column(String, default="informational")  # immediate, within_5min, within_15min, informational
    full_kimi_response = Column(JSONB, nullable=True)

    def to_dict(self):
        return {
            "id": str(self.id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "affected_intersections": [str(i) for i in (self.affected_intersections or [])],
            "decision_type": self.decision_type,
            "action": self.action,
            "explanation": self.explanation,
            "expected_outcome": self.expected_outcome,
            "emission_impact": self.emission_impact,
            "confidence": self.confidence,
            "requires_approval": self.requires_approval,
            "approved_by": self.approved_by,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "urgency": self.urgency,
        }
