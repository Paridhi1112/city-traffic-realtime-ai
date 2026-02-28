"""
Data Aggregator — Combines all fetcher outputs into unified TrafficState per intersection.
Writes to Redis (90s cache) + periodic TimescaleDB flush.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from config import get_settings
from data_fetchers.tomtom_fetcher import fetch_traffic_flow
from data_fetchers.here_fetcher import fetch_here_flow, fetch_here_incidents
from data_fetchers.weather_fetcher import fetch_weather
from data_fetchers.events_fetcher import fetch_events, flag_high_impact_events
from data_fetchers.gtfs_fetcher import fetch_transit_data
from db.redis_manager import RedisStateManager, get_redis

logger = logging.getLogger(__name__)
settings = get_settings()

# Track last DB write time for 5-min flush
_last_db_flush = None


async def aggregate_all_data(intersections: list[dict]) -> dict:
    """Run all fetchers and combine into unified city state.
    Returns the full aggregated state dict.
    """
    import asyncio

    # Run all fetchers in parallel
    tomtom_task = asyncio.create_task(fetch_traffic_flow(intersections))
    here_flow_task = asyncio.create_task(fetch_here_flow(intersections))
    here_incidents_task = asyncio.create_task(fetch_here_incidents(intersections))
    weather_task = asyncio.create_task(fetch_weather())
    events_task = asyncio.create_task(fetch_events())
    transit_task = asyncio.create_task(fetch_transit_data(intersections))

    tomtom_data = await tomtom_task
    here_flow_data = await here_flow_task
    here_incidents = await here_incidents_task
    weather_data = await weather_task
    events_data = await events_task
    transit_data = await transit_task

    # Flag high-impact events
    events_data = flag_high_impact_events(events_data, intersections)

    # Build per-intersection unified state
    intersection_states = []
    tomtom_map = {d["intersection_id"]: d for d in tomtom_data}
    here_map = {d["intersection_id"]: d for d in here_flow_data}
    transit_delays = {d["intersection_id"]: d for d in transit_data.get("delays", [])}

    for inter in intersections:
        iid = inter["id"]
        tt = tomtom_map.get(iid, {})
        he = here_map.get(iid, {})
        td = transit_delays.get(iid, {})

        # Merge congestion from multiple sources
        congestion = tt.get("congestion_percent", 0)
        jam_factor = he.get("jam_factor", 0)

        # Cross-validate: average if both available
        if congestion > 0 and jam_factor > 0:
            # Normalize jam_factor (0-10) to percent (0-100)
            jam_as_pct = jam_factor * 10
            congestion = (congestion + jam_as_pct) / 2

        # Find incidents for this intersection
        intersection_incidents = [
            inc for inc in here_incidents
            if inc.get("intersection_id") == iid
        ]

        # Find nearby events
        nearby_events = [
            ev for ev in events_data
            if iid in ev.get("affected_intersections", [])
        ]

        state = {
            "intersection_id": iid,
            "lat": inter["lat"],
            "lng": inter["lng"],
            "road_names": inter.get("road_names", []),
            "congestion_percent": round(congestion, 1),
            "jam_factor": round(jam_factor, 1),
            "current_speed_kmh": tt.get("current_speed_kmh", 0),
            "freeflow_speed_kmh": tt.get("freeflow_speed_kmh", 50),
            "active_incidents": intersection_incidents,
            "weather_impact_factor": weather_data.get("weather_impact_factor", 1.0),
            "nearby_events": [{"name": e["name"], "attendance": e.get("expected_attendance", 0)} for e in nearby_events],
            "transit_delay_minutes": td.get("delay_minutes", 0),
            "data_source": tt.get("source", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        intersection_states.append(state)

    # Build city-wide state
    avg_congestion = sum(s["congestion_percent"] for s in intersection_states) / max(len(intersection_states), 1)
    city_state = {
        "city_name": settings.city_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_intersections": len(intersection_states),
        "average_congestion_percent": round(avg_congestion, 1),
        "weather": weather_data,
        "active_events": events_data,
        "transit_summary": {
            "total_buses": transit_data.get("total_active_buses", 0),
            "avg_delay_minutes": transit_data.get("average_delay_minutes", 0),
        },
        "active_incidents_count": len(here_incidents),
        "intersections": intersection_states,
    }

    # Store in Redis
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        await rsm.set_city_state(city_state)
        await rsm.set_weather(weather_data)
        await rsm.set_events(events_data)

        for state in intersection_states:
            await rsm.set_intersection_state(state["intersection_id"], state)

        # Update datasource status
        await rsm.set_datasource_status({
            "tomtom": {"status": "ok" if tomtom_data else "error", "last_check": datetime.now(timezone.utc).isoformat()},
            "here": {"status": "ok" if here_flow_data else "error", "last_check": datetime.now(timezone.utc).isoformat()},
            "open_meteo": {"status": "ok" if weather_data.get("source") != "simulated" else "simulated", "last_check": datetime.now(timezone.utc).isoformat()},
            "ticketmaster": {"status": "ok" if any(e.get("source") == "ticketmaster" for e in events_data) else "simulated", "last_check": datetime.now(timezone.utc).isoformat()},
            "overpass_api": {"status": "cached", "last_check": datetime.now(timezone.utc).isoformat()},
            "gtfs": {"status": "simulated", "last_check": datetime.now(timezone.utc).isoformat()},
        })
    except Exception as e:
        logger.error(f"Redis write failed: {e}")

    logger.info(
        f"Aggregated data: {len(intersection_states)} intersections, "
        f"avg congestion {avg_congestion:.1f}%, "
        f"{len(here_incidents)} incidents"
    )
    return city_state


async def write_to_timescaledb(city_state: dict):
    """Flush aggregated state to TimescaleDB (every 5 minutes)."""
    from db.database import async_session_factory
    from models.traffic_state import TrafficState

    try:
        async with async_session_factory() as session:
            for istate in city_state.get("intersections", []):
                ts = TrafficState(
                    id=uuid.uuid4(),
                    intersection_id=istate["intersection_id"],
                    congestion_percent=istate["congestion_percent"],
                    jam_factor=istate["jam_factor"],
                    current_speed_kmh=istate["current_speed_kmh"],
                    freeflow_speed_kmh=istate["freeflow_speed_kmh"],
                    weather_impact_factor=istate["weather_impact_factor"],
                    data_source=istate.get("data_source", "aggregated"),
                )
                session.add(ts)
            await session.commit()
        logger.info(f"Flushed {len(city_state.get('intersections', []))} states to TimescaleDB")
    except Exception as e:
        logger.error(f"TimescaleDB write failed: {e}")
