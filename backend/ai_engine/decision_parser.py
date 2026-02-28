"""
Decision Parser — Parses Kimi JSON response into structured decisions.
"""

import json
import logging
import uuid

logger = logging.getLogger(__name__)


def parse_ai_response(raw_content: str) -> dict:
    """Parse the raw JSON response from Kimi into structured decisions."""
    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Kimi response as JSON: {e}")
        # Try to extract JSON from markdown code block
        if "```json" in raw_content:
            try:
                json_str = raw_content.split("```json")[1].split("```")[0].strip()
                data = json.loads(json_str)
            except Exception:
                return _error_response(raw_content)
        elif "```" in raw_content:
            try:
                json_str = raw_content.split("```")[1].split("```")[0].strip()
                data = json.loads(json_str)
            except Exception:
                return _error_response(raw_content)
        else:
            return _error_response(raw_content)

    # Validate and normalize
    result = {
        "city_summary": data.get("city_summary", "No summary available"),
        "congestion_hotspots": data.get("congestion_hotspots", []),
        "decisions": [],
        "proactive_warnings": data.get("proactive_warnings", []),
        "emission_status": data.get("emission_status", {}),
    }

    for dec in data.get("decisions", []):
        result["decisions"].append({
            "decision_id": dec.get("decision_id", str(uuid.uuid4())),
            "type": dec.get("type", "alert"),
            "affected_intersections": dec.get("affected_intersections", []),
            "action": dec.get("action", "No action specified"),
            "explanation": dec.get("explanation", ""),
            "expected_outcome": dec.get("expected_outcome", ""),
            "emission_impact": dec.get("emission_impact", ""),
            "confidence": int(dec.get("confidence", 50)),
            "requires_human_approval": bool(dec.get("requires_human_approval", True)),
            "urgency": dec.get("urgency", "informational"),
        })

    return result


def _error_response(raw: str) -> dict:
    """Return error response when parsing fails."""
    return {
        "city_summary": "Error parsing AI response",
        "congestion_hotspots": [],
        "decisions": [],
        "proactive_warnings": [],
        "emission_status": {},
        "_parse_error": True,
        "_raw": raw[:500],
    }
