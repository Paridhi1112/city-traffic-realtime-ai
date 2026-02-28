"""
Weather Fetcher — Open-Meteo (primary, no key) + OpenWeatherMap (fallback).
Calculates weather_impact_factor for traffic predictions.
"""

import logging
import random
from datetime import datetime, timezone
from typing import Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
OWM_URL = "https://api.openweathermap.org/data/2.5/weather"


def _calculate_impact_factor(
    precipitation_mm: float = 0, visibility_m: float = 10000, wind_kmh: float = 0
) -> float:
    """Calculate weather impact on traffic.
    Returns multiplier: 1.0 = normal, 1.3 = rain, 1.5 = fog, etc.
    """
    factor = 1.0
    if precipitation_mm > 5:
        factor = max(factor, 1.5)
    elif precipitation_mm > 2:
        factor = max(factor, 1.3)
    elif precipitation_mm > 0.5:
        factor = max(factor, 1.15)

    if visibility_m < 200:
        factor = max(factor, 1.5)
    elif visibility_m < 500:
        factor = max(factor, 1.3)
    elif visibility_m < 1000:
        factor = max(factor, 1.15)

    if wind_kmh > 60:
        factor = max(factor, 1.2)

    return round(factor, 2)


def _simulate_weather() -> dict:
    """Generate simulated weather data."""
    conditions = ["Clear", "Cloudy", "Light Rain", "Heavy Rain", "Fog", "Haze"]
    condition = random.choice(conditions)
    precip = {"Clear": 0, "Cloudy": 0, "Light Rain": 1.5, "Heavy Rain": 6, "Fog": 0.2, "Haze": 0}
    vis = {"Clear": 10000, "Cloudy": 8000, "Light Rain": 5000, "Heavy Rain": 2000, "Fog": 300, "Haze": 3000}

    precipitation = precip.get(condition, 0) + random.uniform(-0.5, 0.5)
    precipitation = max(0, precipitation)
    visibility = vis.get(condition, 10000) + random.uniform(-500, 500)
    visibility = max(100, visibility)
    wind = random.uniform(5, 30)
    temp = random.uniform(22, 38)  # Mumbai temperature range

    return {
        "condition": condition,
        "temperature_c": round(temp, 1),
        "humidity_percent": random.randint(40, 95),
        "precipitation_mm": round(precipitation, 1),
        "visibility_m": round(visibility),
        "wind_speed_kmh": round(wind, 1),
        "weather_impact_factor": _calculate_impact_factor(precipitation, visibility, wind),
        "source": "simulated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "forecast_3h": [
            {
                "hour_offset": h,
                "precipitation_mm": round(max(0, precipitation + random.uniform(-2, 2)), 1),
                "condition": random.choice(conditions),
            }
            for h in [1, 2, 3]
        ],
    }


async def fetch_weather() -> dict:
    """Fetch current weather + 3hr forecast. Open-Meteo primary, OWM fallback."""
    if settings.simulation_mode:
        return _simulate_weather()

    lat, lng = settings.city_center

    # Try Open-Meteo first (free, no key)
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                OPEN_METEO_URL,
                params={
                    "latitude": lat,
                    "longitude": lng,
                    "current": "temperature_2m,relative_humidity_2m,precipitation,visibility,wind_speed_10m,weather_code",
                    "hourly": "precipitation,visibility,wind_speed_10m",
                    "forecast_hours": 4,
                    "timezone": "auto",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        current = data.get("current", {})
        hourly = data.get("hourly", {})

        precip = current.get("precipitation", 0) or 0
        vis = current.get("visibility", 10000) or 10000
        wind = current.get("wind_speed_10m", 0) or 0

        # Weather code to condition
        code = current.get("weather_code", 0)
        condition = _weather_code_to_condition(code)

        forecast_3h = []
        precip_h = hourly.get("precipitation", [0, 0, 0, 0])
        for h in range(1, min(4, len(precip_h))):
            forecast_3h.append({
                "hour_offset": h,
                "precipitation_mm": round(precip_h[h] or 0, 1),
                "condition": "Forecast",
            })

        return {
            "condition": condition,
            "temperature_c": round(current.get("temperature_2m", 30), 1),
            "humidity_percent": current.get("relative_humidity_2m", 60),
            "precipitation_mm": round(precip, 1),
            "visibility_m": round(vis),
            "wind_speed_kmh": round(wind, 1),
            "weather_impact_factor": _calculate_impact_factor(precip, vis, wind),
            "source": "open_meteo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "forecast_3h": forecast_3h,
        }

    except Exception as e:
        logger.warning(f"Open-Meteo failed: {e}, trying OpenWeatherMap")

    # Fallback to OWM
    if settings.openweathermap_api_key:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    OWM_URL,
                    params={
                        "lat": lat,
                        "lon": lng,
                        "appid": settings.openweathermap_api_key,
                        "units": "metric",
                    },
                )
                resp.raise_for_status()
                data = resp.json()

            rain = data.get("rain", {}).get("1h", 0)
            vis = data.get("visibility", 10000)
            wind = data.get("wind", {}).get("speed", 0) * 3.6  # m/s to km/h

            return {
                "condition": data.get("weather", [{}])[0].get("main", "Unknown"),
                "temperature_c": round(data.get("main", {}).get("temp", 30), 1),
                "humidity_percent": data.get("main", {}).get("humidity", 60),
                "precipitation_mm": round(rain, 1),
                "visibility_m": round(vis),
                "wind_speed_kmh": round(wind, 1),
                "weather_impact_factor": _calculate_impact_factor(rain, vis, wind),
                "source": "openweathermap",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "forecast_3h": [],
            }
        except Exception as e:
            logger.error(f"OWM also failed: {e}")

    logger.warning("All weather sources failed — using simulated data")
    return _simulate_weather()


def _weather_code_to_condition(code: int) -> str:
    """Convert WMO weather code to human-readable condition."""
    if code == 0:
        return "Clear"
    elif code in (1, 2, 3):
        return "Cloudy"
    elif code in (45, 48):
        return "Fog"
    elif code in (51, 53, 55, 56, 57):
        return "Drizzle"
    elif code in (61, 63, 65, 66, 67):
        return "Rain"
    elif code in (71, 73, 75, 77):
        return "Snow"
    elif code in (80, 81, 82):
        return "Heavy Rain"
    elif code in (95, 96, 99):
        return "Thunderstorm"
    return "Unknown"
