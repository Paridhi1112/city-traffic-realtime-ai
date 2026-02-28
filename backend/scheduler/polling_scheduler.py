"""
APScheduler Polling Scheduler — triggers all data fetchers on schedule.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

scheduler = AsyncIOScheduler()


def setup_scheduler(intersections: list[dict]):
    """Configure and start all scheduled jobs."""
    from scheduler.jobs import (
        job_fetch_all_data,
        job_run_predictions,
        job_run_ai_decisions,
        job_flush_to_db,
    )

    # Main data collection — every 60s
    scheduler.add_job(
        job_fetch_all_data,
        IntervalTrigger(seconds=settings.polling_interval_seconds),
        args=[intersections],
        id="fetch_all_data",
        name="Fetch All Data Sources",
        replace_existing=True,
    )

    # Run predictions — every 5 min
    scheduler.add_job(
        job_run_predictions,
        IntervalTrigger(minutes=5),
        args=[intersections],
        id="run_predictions",
        name="Run Congestion Predictions",
        replace_existing=True,
    )

    # AI decisions — every 2 min
    scheduler.add_job(
        job_run_ai_decisions,
        IntervalTrigger(seconds=settings.ai_decision_interval_seconds),
        args=[intersections],
        id="run_ai_decisions",
        name="Run AI Decision Loop",
        replace_existing=True,
    )

    # Flush to TimescaleDB — every 5 min
    scheduler.add_job(
        job_flush_to_db,
        IntervalTrigger(minutes=5),
        id="flush_to_db",
        name="Flush to TimescaleDB",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler started with all jobs")


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
