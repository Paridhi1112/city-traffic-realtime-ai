"""
Events Fetcher — Ticketmaster events + Public Holiday API.
Flags events near intersections as high-impact.
Now generates a stable weekly calendar of upcoming events.
"""

import logging
import random
import hashlib
from datetime import datetime, timezone, timedelta
from math import radians, sin, cos, sqrt, atan2

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

TICKETMASTER_URL = "https://app.ticketmaster.com/discovery/v2/events.json"
HOLIDAY_URL = "https://date.nager.at/api/v3/PublicHolidays"

# City timezone mapping
CITY_TIMEZONES = {
    "Mumbai": {"tz_name": "Asia/Kolkata", "utc_offset": "+05:30", "abbr": "IST"},
    "Delhi": {"tz_name": "Asia/Kolkata", "utc_offset": "+05:30", "abbr": "IST"},
    "Bangalore": {"tz_name": "Asia/Kolkata", "utc_offset": "+05:30", "abbr": "IST"},
    "New York": {"tz_name": "America/New_York", "utc_offset": "-05:00", "abbr": "EST"},
    "London": {"tz_name": "Europe/London", "utc_offset": "+00:00", "abbr": "GMT"},
    "Tokyo": {"tz_name": "Asia/Tokyo", "utc_offset": "+09:00", "abbr": "JST"},
    "Singapore": {"tz_name": "Asia/Singapore", "utc_offset": "+08:00", "abbr": "SGT"},
    "Dubai": {"tz_name": "Asia/Dubai", "utc_offset": "+04:00", "abbr": "GST"},
}

# Full weekly event templates per category
EVENT_TEMPLATES = {
    "sports": [
        {"name": "IPL Cricket Match — Wankhede Stadium", "attendance": 33000, "lat": 18.939, "lng": 72.826, "duration_hours": 4},
        {"name": "Mumbai Indians Practice Match", "attendance": 5000, "lat": 19.063, "lng": 72.871, "duration_hours": 3},
        {"name": "Inter-School Football Tournament", "attendance": 2000, "lat": 19.117, "lng": 72.857, "duration_hours": 5},
        {"name": "Maharashtra State Swimming Championship", "attendance": 1500, "lat": 19.022, "lng": 72.843, "duration_hours": 6},
        {"name": "Weekend Marathon — Marine Drive", "attendance": 8000, "lat": 18.944, "lng": 72.824, "duration_hours": 4},
    ],
    "entertainment": [
        {"name": "Bollywood Concert — MMRDA Grounds", "attendance": 15000, "lat": 19.063, "lng": 72.871, "duration_hours": 3},
        {"name": "Comedy Night at NCPA", "attendance": 800, "lat": 18.927, "lng": 72.822, "duration_hours": 2},
        {"name": "Jazz Festival — Bandra Fort", "attendance": 3000, "lat": 19.044, "lng": 72.821, "duration_hours": 4},
        {"name": "Film Premiere — PVR Phoenix", "attendance": 1200, "lat": 19.001, "lng": 72.828, "duration_hours": 3},
    ],
    "festival": [
        {"name": "Religious Festival — Siddhivinayak Temple", "attendance": 20000, "lat": 19.017, "lng": 72.830, "duration_hours": 12},
        {"name": "Ganesh Chaturthi Procession — Lalbaug", "attendance": 50000, "lat": 18.996, "lng": 72.842, "duration_hours": 8},
        {"name": "Dahi Handi Celebration — Dadar", "attendance": 10000, "lat": 19.019, "lng": 72.844, "duration_hours": 6},
    ],
    "exhibition": [
        {"name": "Trade Exhibition — BKC Convention Centre", "attendance": 5000, "lat": 19.059, "lng": 72.866, "duration_hours": 8},
        {"name": "Auto Expo — NESCO Grounds", "attendance": 12000, "lat": 19.141, "lng": 72.859, "duration_hours": 10},
        {"name": "Art Exhibition — Jehangir Art Gallery", "attendance": 1000, "lat": 18.928, "lng": 72.831, "duration_hours": 6},
    ],
    "public": [
        {"name": "Municipal Road Work — Eastern Express Highway", "attendance": 0, "lat": 19.075, "lng": 72.878, "duration_hours": 10},
        {"name": "Water Pipeline Maintenance — Andheri", "attendance": 0, "lat": 19.119, "lng": 72.847, "duration_hours": 8},
        {"name": "Political Rally — Azad Maidan", "attendance": 15000, "lat": 18.940, "lng": 72.833, "duration_hours": 4},
    ],
}

CATEGORY_COLORS = {
    "sports": "#3b82f6",
    "entertainment": "#ec4899",
    "festival": "#f59e0b",
    "exhibition": "#8b5cf6",
    "public": "#6b7280",
}


def _get_city_timezone() -> dict:
    """Get timezone info for the current city."""
    return CITY_TIMEZONES.get(settings.city_name, {
        "tz_name": "UTC", "utc_offset": "+00:00", "abbr": "UTC"
    })


def _generate_weekly_events() -> list[dict]:
    """Generate a deterministic set of events for the next 7 days.
    Uses a date-based seed so events are stable within the same day.
    """
    now = datetime.now(timezone.utc)
    today = now.date()

    # Create a deterministic seed based on today's date + city name
    seed_str = f"{today.isoformat()}-{settings.city_name}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    tz_info = _get_city_timezone()
    events = []

    # Generate events for each of the next 7 days
    for day_offset in range(7):
        event_date = today + timedelta(days=day_offset)
        day_name = event_date.strftime("%A")  # Monday, Tuesday, etc.

        # Determine how many events for this day (2-4 per day)
        num_events = rng.randint(2, 4)

        # Build a pool of all templates
        all_templates = []
        for category, templates in EVENT_TEMPLATES.items():
            for t in templates:
                all_templates.append({**t, "category": category})

        # Pick random events for this day
        day_events = rng.sample(all_templates, min(num_events, len(all_templates)))

        for template in day_events:
            # Generate a random start hour between 7 AM and 9 PM
            start_hour = rng.randint(7, 21)
            start_minute = rng.choice([0, 15, 30, 45])

            start_dt = datetime(
                event_date.year, event_date.month, event_date.day,
                start_hour, start_minute, 0,
                tzinfo=timezone.utc
            )
            end_dt = start_dt + timedelta(hours=template.get("duration_hours", 3))

            events.append({
                "name": template["name"],
                "source": "simulated",
                "category": template["category"],
                "category_color": CATEGORY_COLORS.get(template["category"], "#6b7280"),
                "lat": template["lat"],
                "lng": template["lng"],
                "radius_meters": 2000,
                "expected_attendance": template["attendance"],
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "date": event_date.isoformat(),
                "day_of_week": day_name,
                "duration_hours": template.get("duration_hours", 3),
                "is_today": day_offset == 0,
                "is_tomorrow": day_offset == 1,
                "day_offset": day_offset,
            })

    return events


def _simulate_events() -> list[dict]:
    """Generate simulated city events — returns only today's active events."""
    weekly = _generate_weekly_events()
    return [e for e in weekly if e.get("is_today", False)]


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
                    "category": "entertainment",
                    "category_color": CATEGORY_COLORS["entertainment"],
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
                    "category": "public",
                    "category_color": CATEGORY_COLORS["public"],
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


async def fetch_weekly_events() -> dict:
    """Fetch the full weekly event calendar with timezone info."""
    tz_info = _get_city_timezone()
    now = datetime.now(timezone.utc)

    if settings.simulation_mode:
        weekly = _generate_weekly_events()
        holidays = _simulate_holidays()
        all_events = weekly + holidays
    else:
        all_events = _generate_weekly_events()  # Fallback

    # Group events by day
    days = {}
    for event in all_events:
        day_key = event.get("date", now.date().isoformat())
        if day_key not in days:
            days[day_key] = {
                "date": day_key,
                "day_of_week": event.get("day_of_week", ""),
                "is_today": event.get("is_today", False),
                "is_tomorrow": event.get("is_tomorrow", False),
                "events": [],
            }
        days[day_key]["events"].append(event)

    # Sort by date
    sorted_days = sorted(days.values(), key=lambda d: d["date"])

    return {
        "city_name": settings.city_name,
        "timezone": tz_info,
        "current_time": now.isoformat(),
        "total_events": len(all_events),
        "days": sorted_days,
    }


def _simulate_holidays() -> list[dict]:
    """Occasionally simulate a holiday."""
    # Use deterministic check based on date
    today = datetime.now(timezone.utc).date()
    seed_str = f"holiday-{today.isoformat()}-{settings.city_name}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)

    if rng.random() < 0.15:  # ~15% chance per day
        lat, lng = settings.city_center
        return [{
            "name": "Holiday: Simulated Public Holiday",
            "source": "holiday_simulated",
            "category": "public",
            "category_color": CATEGORY_COLORS["public"],
            "lat": lat,
            "lng": lng,
            "radius_meters": 50000,
            "expected_attendance": 0,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "end_time": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "date": today.isoformat(),
            "day_of_week": today.strftime("%A"),
            "is_today": True,
            "is_tomorrow": False,
            "day_offset": 0,
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
