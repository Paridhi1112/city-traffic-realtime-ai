"""
Explainer — Generates human-readable decision explanations.
"""


def explain_decision(decision: dict) -> str:
    """Generate a plain English explanation for city officials."""
    urgency_map = {
        "immediate": "⚠️ IMMEDIATE ACTION REQUIRED",
        "within_5min": "🔶 Action needed within 5 minutes",
        "within_15min": "🔷 Action needed within 15 minutes",
        "informational": "ℹ️ For your information",
    }

    type_map = {
        "signal_adjustment": "🚦 Signal Timing Change",
        "reroute_suggestion": "🔀 Route Diversion",
        "alert": "🔔 Traffic Alert",
        "preemptive_action": "🎯 Preemptive Action",
    }

    urgency = urgency_map.get(decision.get("urgency", "informational"), "ℹ️ Info")
    dtype = type_map.get(decision.get("type", "alert"), "🔔 Alert")
    confidence = decision.get("confidence", 50)
    approval = "Requires approval" if decision.get("requires_human_approval") else "Auto-executable"

    explanation = f"""
{urgency}
{dtype} | Confidence: {confidence}% | {approval}

ACTION: {decision.get('action', 'No action')}

WHY: {decision.get('explanation', 'No explanation')}

EXPECTED RESULT: {decision.get('expected_outcome', 'Unknown')}

EMISSION IMPACT: {decision.get('emission_impact', 'Not estimated')}
""".strip()

    return explanation


def format_city_summary(ai_result: dict) -> dict:
    """Format full AI result into a dashboard-friendly summary."""
    return {
        "summary_text": ai_result.get("city_summary", "No data available"),
        "hotspot_count": len(ai_result.get("congestion_hotspots", [])),
        "decision_count": len(ai_result.get("decisions", [])),
        "warning_count": len(ai_result.get("proactive_warnings", [])),
        "decisions_explained": [
            {
                **dec,
                "explanation_formatted": explain_decision(dec),
            }
            for dec in ai_result.get("decisions", [])
        ],
        "emission_status": ai_result.get("emission_status", {}),
    }
