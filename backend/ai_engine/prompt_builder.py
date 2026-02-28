"""
Prompt Builder — Assembles system + user prompts for Kimi AI.
"""

import json
from datetime import datetime, timezone
from config import get_settings

settings = get_settings()

SYSTEM_PROMPT = """You are Urban Traffic Brain, an AI system managing city-wide traffic.
You receive real-time data from multiple sources about every major intersection.
Analyze the entire city simultaneously and make coordinated decisions.

Your decisions must consider:
- Current congestion levels across all intersections
- Predicted congestion in next 60 minutes
- Active incidents and road closures
- Weather conditions and their traffic impact
- Upcoming events that will cause localized surges
- Public transit delays that push people to roads

For each response return a valid JSON object with this exact schema:
{
  "city_summary": "one paragraph overview of current city traffic health",
  "congestion_hotspots": [
    {"intersection_id": "", "reason": "", "severity": "low|medium|high|critical"}
  ],
  "decisions": [
    {
      "decision_id": "uuid",
      "type": "signal_adjustment|reroute_suggestion|alert|preemptive_action",
      "affected_intersections": [],
      "action": "specific action description",
      "explanation": "plain English explanation for city official",
      "expected_outcome": "specific measurable outcome",
      "emission_impact": "estimated CO2 reduction/increase in kg",
      "confidence": 0-100,
      "requires_human_approval": true|false,
      "urgency": "immediate|within_5min|within_15min|informational"
    }
  ],
  "proactive_warnings": [
    {"message": "", "time_until_impact_minutes": 0, "affected_area": ""}
  ],
  "emission_status": {
    "current_city_emission_rate": "",
    "vs_normal_baseline": "",
    "biggest_emission_source": ""
  }
}

Respond only in valid JSON. Do not include any text outside the JSON object."""


def build_system_prompt() -> str:
    return SYSTEM_PROMPT


def build_user_prompt(city_state: dict, recent_decisions: list = None) -> str:
    """Build the user prompt from live city state data."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    weather = city_state.get("weather", {})
    intersections = city_state.get("intersections", [])

    # Compact intersection data
    intersection_data = []
    for i in intersections:
        intersection_data.append({
            "id": i["intersection_id"],
            "name": i.get("road_names", ["Unknown"])[0] if i.get("road_names") else "Unknown",
            "congestion_%": i["congestion_percent"],
            "jam_factor": i["jam_factor"],
            "speed_kmh": i["current_speed_kmh"],
            "freeflow_kmh": i["freeflow_speed_kmh"],
            "incidents": len(i.get("active_incidents", [])),
            "events_nearby": len(i.get("nearby_events", [])),
            "transit_delay_min": i.get("transit_delay_minutes", 0),
        })

    # Active incidents
    incidents_list = []
    for i in intersections:
        for inc in i.get("active_incidents", []):
            incidents_list.append({
                "intersection": i["intersection_id"],
                "type": inc.get("incident_type", "unknown"),
                "severity": inc.get("severity", 0),
                "description": inc.get("description", ""),
            })

    # Events
    events_list = city_state.get("active_events", [])

    weather_summary = (
        f"{weather.get('condition', 'Unknown')}, "
        f"{weather.get('temperature_c', 'N/A')}°C, "
        f"Rain: {weather.get('precipitation_mm', 0)}mm/hr, "
        f"Visibility: {weather.get('visibility_m', 'N/A')}m"
    )

    prompt = f"""Current time: {now}
City: {settings.city_name}
Weather: {weather_summary} (impact factor: {weather.get('weather_impact_factor', 1.0)})

LIVE INTERSECTION DATA ({len(intersection_data)} intersections):
{json.dumps(intersection_data, indent=1)}

ACTIVE INCIDENTS:
{json.dumps(incidents_list, indent=1) if incidents_list else "None"}

UPCOMING EVENTS (next 4 hours):
{json.dumps([{"name": e.get("name"), "attendance": e.get("expected_attendance", 0)} for e in events_list], indent=1) if events_list else "None"}

LAST 3 DECISIONS AND OUTCOMES:
{json.dumps(recent_decisions[:3] if recent_decisions else [], indent=1)}

Analyze the full city state and provide your decisions."""

    return prompt
