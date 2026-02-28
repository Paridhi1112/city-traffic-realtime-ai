"""
Kimi AI Client — Uses OpenAI SDK with base_url override for Moonshot API.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from config import get_settings
from ai_engine.prompt_builder import build_system_prompt, build_user_prompt
from ai_engine.decision_parser import parse_ai_response
from ai_engine.memory_manager import get_recent_decisions
from db.redis_manager import get_redis, RedisStateManager

logger = logging.getLogger(__name__)
settings = get_settings()


def _generate_simulated_decisions(city_state: dict) -> dict:
    """Generate simulated AI decisions for demo mode."""
    import random

    intersections = city_state.get("intersections", [])
    # Sort by congestion to find hotspots
    hotspots = sorted(intersections, key=lambda x: x.get("congestion_percent", 0), reverse=True)[:5]

    avg_congestion = city_state.get("average_congestion_percent", 30)
    health = "smooth" if avg_congestion < 30 else "moderate" if avg_congestion < 60 else "heavily congested"

    decisions = []
    for i, hs in enumerate(hotspots[:3]):
        decision_types = ["signal_adjustment", "reroute_suggestion", "alert", "preemptive_action"]
        actions = [
            f"Extend green phase by 15 seconds on main approach at {hs.get('road_names', ['intersection'])[0] if hs.get('road_names') else 'intersection'}",
            f"Suggest rerouting traffic via alternate road to reduce load at this junction",
            f"Deploy dynamic message sign warning: 'Congestion ahead — expect {int(hs.get('congestion_percent', 50))}% delays'",
            f"Pre-emptively adjust signal timing based on predicted congestion increase in 30 minutes",
        ]

        decisions.append({
            "decision_id": str(uuid.uuid4()),
            "type": decision_types[i % len(decision_types)],
            "affected_intersections": [hs["intersection_id"]],
            "action": actions[i % len(actions)],
            "explanation": f"Congestion at {hs.get('congestion_percent', 0):.0f}% detected. This action will help reduce wait times.",
            "expected_outcome": f"Reduce congestion by {random.randint(10, 25)}% within 15 minutes",
            "emission_impact": f"-{random.randint(5, 20)} kg CO2/hr estimated reduction",
            "confidence": random.randint(60, 95),
            "requires_human_approval": random.random() > 0.5,
            "urgency": random.choice(["immediate", "within_5min", "within_15min", "informational"]),
        })

    return {
        "city_summary": f"City traffic is currently {health} with average congestion at {avg_congestion:.0f}%. "
                       f"Weather impact factor is {city_state.get('weather', {}).get('weather_impact_factor', 1.0)}. "
                       f"{city_state.get('active_incidents_count', 0)} active incidents reported.",
        "congestion_hotspots": [
            {
                "intersection_id": hs["intersection_id"],
                "reason": f"High congestion at {hs.get('congestion_percent', 0):.0f}% — "
                         + (f"incident reported" if hs.get("active_incidents") else "peak hour traffic"),
                "severity": "critical" if hs.get("congestion_percent", 0) > 80 else "high" if hs.get("congestion_percent", 0) > 60 else "medium",
            }
            for hs in hotspots[:5]
        ],
        "decisions": decisions,
        "proactive_warnings": [
            {
                "message": f"Weather-related slowdown expected — impact factor {city_state.get('weather', {}).get('weather_impact_factor', 1.0)}",
                "time_until_impact_minutes": 30,
                "affected_area": "City-wide",
            }
        ] if city_state.get("weather", {}).get("weather_impact_factor", 1.0) > 1.1 else [],
        "emission_status": {
            "current_city_emission_rate": f"{random.randint(800, 2000)} kg CO2/hr",
            "vs_normal_baseline": f"+{random.randint(0, 30)}% above normal",
            "biggest_emission_source": hotspots[0].get("road_names", ["Unknown road"])[0] if hotspots and hotspots[0].get("road_names") else "Major corridor",
        },
    }


async def get_ai_decisions(intersections: list[dict]) -> dict:
    """Get AI decisions — real Kimi API or simulated."""
    # Get current state from Redis
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        city_state = await rsm.get_city_state()
    except Exception:
        city_state = None

    if not city_state:
        logger.warning("No city state in Redis — skipping AI decisions")
        return {"decisions": [], "city_summary": "No data available"}

    # Simulation mode or no API key
    if settings.simulation_mode or not settings.kimi_api_key:
        result = _generate_simulated_decisions(city_state)
        # Store decisions
        await _store_decisions(result, rsm)
        return result

    # Real Kimi API call
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(
            api_key=settings.kimi_api_key,
            base_url=settings.kimi_base_url,
        )

        system_prompt = build_system_prompt()
        recent_decisions = await get_recent_decisions(rsm)
        user_prompt = build_user_prompt(city_state, recent_decisions)

        response = await client.chat.completions.create(
            model=settings.kimi_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )

        raw_content = response.choices[0].message.content
        result = parse_ai_response(raw_content)
        result["_raw_response"] = raw_content
        await _store_decisions(result, rsm)
        return result

    except Exception as e:
        logger.error(f"Kimi API call failed: {e}, falling back to simulated")
        result = _generate_simulated_decisions(city_state)
        await _store_decisions(result, rsm)
        return result


async def _store_decisions(result: dict, rsm: RedisStateManager):
    """Store decisions in Redis and DB."""
    try:
        await rsm.set_last_decisions(result.get("decisions", []))
    except Exception as e:
        logger.error(f"Failed to store decisions in Redis: {e}")

    # Store in DB
    try:
        from db.database import async_session_factory
        from models.decision import AIDecision

        async with async_session_factory() as session:
            for dec in result.get("decisions", []):
                ai_dec = AIDecision(
                    id=uuid.uuid4(),
                    decision_type=dec.get("type", "unknown"),
                    affected_intersections=dec.get("affected_intersections", []),
                    action=dec.get("action", ""),
                    explanation=dec.get("explanation", ""),
                    expected_outcome=dec.get("expected_outcome", ""),
                    emission_impact=dec.get("emission_impact", ""),
                    confidence=dec.get("confidence", 50),
                    requires_approval=dec.get("requires_human_approval", True),
                    urgency=dec.get("urgency", "informational"),
                    full_kimi_response=result,
                )
                session.add(ai_dec)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to store decisions in DB: {e}")
