"""
Feature Builder — Constructs feature vectors for XGBoost from live data.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timezone


FEATURE_COLUMNS = [
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "is_holiday",
    "month",
    "current_congestion_percent",
    "current_jam_factor",
    "weather_precipitation_mm",
    "weather_visibility_m",
    "weather_impact_factor",
    "has_nearby_event",
    "event_expected_attendance",
    "has_active_incident",
    "incident_severity",
    "transit_delay_minutes",
    "historical_avg_congestion_this_hour",
    "historical_avg_congestion_same_weekday",
]


def build_features_for_intersection(intersection_state: dict, weather: dict = None) -> np.ndarray:
    """Build a feature vector for one intersection."""
    now = datetime.now(timezone.utc)

    incidents = intersection_state.get("active_incidents", [])
    events = intersection_state.get("nearby_events", [])
    max_severity = max((inc.get("severity", 0) for inc in incidents), default=0)
    max_attendance = max((ev.get("attendance", 0) for ev in events), default=0)

    if weather is None:
        weather = {}

    features = [
        now.hour,                                                   # hour_of_day
        now.weekday(),                                              # day_of_week
        1 if now.weekday() >= 5 else 0,                            # is_weekend
        0,                                                          # is_holiday (set by caller)
        now.month,                                                  # month
        intersection_state.get("congestion_percent", 0),           # current_congestion_percent
        intersection_state.get("jam_factor", 0),                   # current_jam_factor
        weather.get("precipitation_mm", 0),                        # weather_precipitation_mm
        weather.get("visibility_m", 10000),                        # weather_visibility_m
        weather.get("weather_impact_factor", 1.0),                 # weather_impact_factor
        1 if events else 0,                                        # has_nearby_event
        max_attendance,                                             # event_expected_attendance
        1 if incidents else 0,                                     # has_active_incident
        max_severity,                                               # incident_severity
        intersection_state.get("transit_delay_minutes", 0),        # transit_delay_minutes
        intersection_state.get("congestion_percent", 30),          # historical_avg (placeholder)
        intersection_state.get("congestion_percent", 30),          # historical_avg (placeholder)
    ]

    return np.array(features, dtype=np.float32).reshape(1, -1)


def build_batch_features(intersection_states: list[dict], weather: dict = None) -> pd.DataFrame:
    """Build feature matrix for all intersections."""
    rows = []
    for state in intersection_states:
        feat = build_features_for_intersection(state, weather).flatten()
        rows.append(feat)

    return pd.DataFrame(rows, columns=FEATURE_COLUMNS)
