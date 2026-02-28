"""
Emissions API Routes.
"""

import random
from fastapi import APIRouter
from db.redis_manager import get_redis, RedisStateManager

router = APIRouter(prefix="/api/emissions", tags=["emissions"])


@router.get("/live")
async def get_live_emissions():
    """Get current city emission estimates based on congestion."""
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        city_state = await rsm.get_city_state()

        if city_state:
            avg_congestion = city_state.get("average_congestion_percent", 0)
            # Rough emission model: higher congestion = more idling = more CO2
            baseline_kg_per_hr = 1200  # Normal city baseline
            congestion_multiplier = 1 + (avg_congestion / 100) * 0.5
            current_rate = baseline_kg_per_hr * congestion_multiplier

            return {
                "current_emission_rate_kg_hr": round(current_rate),
                "baseline_kg_hr": baseline_kg_per_hr,
                "vs_baseline_percent": round((congestion_multiplier - 1) * 100, 1),
                "average_congestion": avg_congestion,
                "timestamp": city_state.get("timestamp"),
                "top_emitters": _get_top_emitters(city_state),
            }
    except Exception:
        pass

    return {
        "current_emission_rate_kg_hr": 0,
        "baseline_kg_hr": 1200,
        "vs_baseline_percent": 0,
    }


@router.get("/report")
async def get_emission_report():
    """Get emission analysis report."""
    return {
        "report": "CO2 emission tracking based on real-time congestion data",
        "methodology": "Emission rate correlates with vehicle idle time and congestion percentage",
        "recommendations": [
            "Optimize signal timing at top congestion hotspots",
            "Promote public transit during peak hours",
            "Implement dynamic tolling for congested corridors",
        ],
    }


def _get_top_emitters(city_state: dict) -> list[dict]:
    """Get top 5 emission-producing intersections."""
    intersections = city_state.get("intersections", [])
    sorted_ints = sorted(intersections, key=lambda x: x.get("congestion_percent", 0), reverse=True)
    return [
        {
            "intersection_id": i["intersection_id"],
            "road_names": i.get("road_names", []),
            "congestion_percent": i.get("congestion_percent", 0),
            "estimated_co2_kg_hr": round(i.get("congestion_percent", 0) * 0.5, 1),
        }
        for i in sorted_ints[:5]
    ]
