"""
Events Fetcher — Ticketmaster events + Public Holiday API.
Flags events near intersections as high-impact.
"""

import logging
import random
from datetime import datetime, timezone, timedelta
from math import radians, sin, cos, sqrt, atan2

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
HOLIDAY_URL = "https://date.nager.at/api/v3/PublicHolidays"


def _simulate_events() -> list[dict]:
    """Generate simulated city events."""
    event_templates = [
        {"name": "IPL Cricket Match — Wankhede Stadium", "attendance": 33000, "lat": 18.939, "lng": 72.826},
        {"name": "Bollywood Concert — MMRDA Grounds", "attendance": 15000, "lat": 19.063, "lng": 72.871},
        {"name": "Marathon — Marine Drive", "attendance": 8000, "lat": 18.944, "lng": 72.824},
        {"name": "Trade Exhibition — BKC", "attendance": 5000, "lat": 19.059, "lng": 72.866},
        {"name": "Religious Festival — Siddhivinayak", "attendance": 20000, "lat": 19.017, "lng": 72.830},
    ]

    now = datetime.now(timezone.utc)
    events = []
    # Generate 0-2 random events
    count = random.randint(0, 2)
    if count > 0:
        for template in random.sample(event_templates, min(count, len(event_templates))):
            start = now + timedelta(hours=random.randint(0, 4))
            events.append({
                "name": template["name"],
                "source": "simulated",
                "lat": template["lat"],
                "lng": template["lng"],
                "radius_meters": 2000,
                "expected_attendance": template["attendance"],
                "start_time": start.isoformat(),
                "end_time": (start + timedelta(hours=random.randint(2, 5))).isoformat(),
            })

    return events


async def fetch_events() -> list[dict]:
    """Fetch today's events from Ticketmaster + check holidays."""
    if settings.simulation_mode:
        events = _simulate_events()
        holidays = _simulate_holidays()
        return events + holidays

    events = []

    # Ticketmaster
    if settings.ticketmaster_api_key:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    TICKETMASTER_URL,
                    params={
                        "apikey": settings.ticketmaster_api_key,
                        "city": settings.city_name,
                        "classificationName": "music,sports",
                        "startDateTime": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "endDateTime": (datetime.now(timezone.utc) + timedelta(hours=12)).strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        ),
                        "size": 10,
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            for event in data.get("_embedded", {}).get("events", []):
                venue = event.get("_embedded", {}).get("venues", [{}])[0]
                loc = venue.get("location", {})
                events.append({
                    "name": event.get("name", "Unknown Event"),
                    "source": "ticketmaster",
                    "lat": float(loc.get("latitude", 0)),
                    "lng": float(loc.get("longitude", 0)),
                    "radius_meters": 2000,
                    "expected_attendance": _estimate_attendance(venue),
                    "start_time": event.get("dates", {}).get("start", {}).get("dateTime"),
                    "end_time": None,
                })
        except Exception as e:
            logger.warning(f"Ticketmaster fetch failed: {e}")

    # Public Holidays
    try:
        year = datetime.now().year
        async with httpx.AsyncClient(timeout=10) as client:
            # Try with country code from city config
            resp = await client.get(f"{HOLIDAY_URL}/{year}/IN")
            resp.raise_for_status()
            holidays = resp.json()

        today = datetime.now().strftime("%Y-%m-%d")
        for h in holidays:
            if h.get("date") == today:
                lat, lng = settings.city_center
                events.append({
                    "name": f"Holiday: {h.get('localName', h.get('name', 'Public Holiday'))}",
                    "source": "holiday_api",
                    "lat": lat,
                    "lng": lng,
                    "radius_meters": 50000,  # City-wide impact
                    "expected_attendance": 0,
                    "start_time": f"{today}T00:00:00Z",
                    "end_time": f"{today}T23:59:59Z",
                })
    except Exception as e:
        logger.warning(f"Holiday API fetch failed: {e}")

    return events if events else _simulate_events()


def _simulate_holidays() -> list[dict]:
    """Occasionally simulate a holiday."""
    if random.random() < 0.1:  # 10% chance
        lat, lng = settings.city_center
        return [{
            "name": "Holiday: Simulated Public Holiday",
            "source": "holiday_simulated",
            "lat": lat,
            "lng": lng,
            "radius_meters": 50000,
            "expected_attendance": 0,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        }]
    return []


def _estimate_attendance(venue: dict) -> int:
    """Estimate event attendance from venue capacity or defaults."""
    cap = venue.get("generalInfo", {}).get("capacity")
    if cap:
        try:
            return int(cap)
        except (ValueError, TypeError):
            pass
    return 5000  # Default estimate


def flag_high_impact_events(events: list[dict], intersections: list[dict]) -> list[dict]:
    """Flag events within 2km of intersections."""
    for event in events:
        if not event.get("lat") or not event.get("lng"):
            continue
        nearby = []
        for inter in intersections:
            dist = _haversine(event["lat"], event["lng"], inter["lat"], inter["lng"])
            if dist < (event.get("radius_meters", 2000) / 1000):
                nearby.append(inter["id"])
        event["affected_intersections"] = nearby
        event["high_impact"] = len(nearby) > 0
    return events


def _haversine(lat1, lng1, lat2, lng2) -> float:
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))
