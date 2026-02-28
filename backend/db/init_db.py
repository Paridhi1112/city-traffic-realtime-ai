"""
Database initialization — creates tables and TimescaleDB hypertables.
"""

import asyncio
import logging
from sqlalchemy import text
from db.database import engine, Base

# Import all models so they are registered with Base
from models.intersection import Intersection  # noqa: F401
from models.traffic_state import TrafficState  # noqa: F401
from models.decision import AIDecision  # noqa: F401
from models.event import CityEvent  # noqa: F401
from models.alert import Alert  # noqa: F401
from models.incident import Incident  # noqa: F401
from models.prediction import Prediction  # noqa: F401

logger = logging.getLogger(__name__)


async def init_database():
    """Create all tables and set up TimescaleDB hypertable."""
    async with engine.begin() as conn:
        # Enable TimescaleDB extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)

        # Convert traffic_states to hypertable (idempotent check)
        try:
            await conn.execute(
                text(
                    "SELECT create_hypertable('traffic_states', 'timestamp', "
                    "if_not_exists => TRUE, migrate_data => TRUE);"
                )
            )
            logger.info("TimescaleDB hypertable 'traffic_states' ready")
        except Exception as e:
            logger.warning(f"Hypertable setup note: {e}")

    logger.info("Database initialization complete")


if __name__ == "__main__":
    asyncio.run(init_database())
