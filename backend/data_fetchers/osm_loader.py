"""
OSM Loader — Fetches intersection data from Overpass API.
Caches to GeoJSON. In simulation mode, generates realistic fake intersections.
"""

import json
import logging
import random
import uuid
from pathlib import Path
from typing import Optional

import httpx

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

GEOJSON_PATH = Path("/app/city_data/intersections.geojson")
OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _generate_simulated_intersections(n: int = 30) -> dict:
    """Generate realistic fake intersections within city bbox for simulation mode."""
    s, w, n_lat, e = settings.city_bbox_tuple
    road_prefixes = [
        "MG Road", "SV Road", "LBS Marg", "Western Express Highway",
        "Eastern Express Highway", "Linking Road", "Hill Road", "Turner Road",
        "Juhu Tara Road", "Peddar Road", "Marine Drive", "Colaba Causeway",
        "FC Road", "JM Road", "Andheri Kurla Road", "Goregaon Mulund Link",
        "Sion Panvel Highway", "Ghodbunder Road", "Thane Belapur Road",
        "Palm Beach Road", "Vashi Bridge", "Airoli Bridge Road",
        "Aarey Road", "JVLR", "Santacruz Chembur Link", "BKC Connector",
        "Wadala Bridge", "Mahalaxmi Race Course", "Haji Ali Junction",
        "Worli Sea Face", "Bandra Reclamation", "Carter Road",
    ]
    features = []
    for i in range(n):
        lat = s + random.random() * (n_lat - s)
        lng = w + random.random() * (e - w)
        roads = random.sample(road_prefixes, k=min(random.randint(2, 3), len(road_prefixes)))
        features.append({
            "type": "Feature",
            "properties": {
                "id": str(uuid.uuid4()),
                "name": f"{roads[0]} × {roads[1]}",
                "road_names": roads,
                "num_lanes": random.choice([2, 3, 4, 6]),
                "speed_limit_kmh": random.choice([30, 40, 50, 60, 80]),
                "zone": random.choice(["South Mumbai", "Bandra-Kurla Complex", "Andheri", "Thane", "Dadar"]),
                "osm_node_id": random.randint(100000000, 999999999),
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lng, lat],
            },
        })
    return {
        "type": "FeatureCollection",
        "features": features,
    }


async def _fetch_from_overpass() -> Optional[dict]:
    """Query Overpass API for traffic signals in city bbox."""
    s, w, n_lat, e = settings.city_bbox_tuple
    query = f"""
    [out:json][timeout:60];
    node["highway"="traffic_signals"]({s},{w},{n_lat},{e});
    out body;
    """
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            resp = await client.post(OVERPASS_URL, data={"data": query})
            resp.raise_for_status()
            data = resp.json()

        if not data.get("elements"):
            logger.warning("Overpass returned no elements")
            return None

        features = []
        for el in data["elements"][:50]:  # Limit to 50 intersections
            features.append({
                "type": "Feature",
                "properties": {
                    "id": str(uuid.uuid4()),
                    "name": el.get("tags", {}).get("name", f"Intersection {el['id']}"),
                    "road_names": [],
                    "num_lanes": 2,
                    "speed_limit_kmh": 50,
                    "zone": "general",
                    "osm_node_id": el["id"],
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [el["lon"], el["lat"]],
                },
            })

        return {"type": "FeatureCollection", "features": features}

    except Exception as e:
        logger.error(f"Overpass API error: {e}")
        return None


async def load_intersections() -> dict:
    """Load intersections from cache or fetch from Overpass / generate simulated."""

    # Check cache first
    if GEOJSON_PATH.exists():
        try:
            with open(GEOJSON_PATH) as f:
                geojson = json.load(f)
            if geojson.get("features"):
                logger.info(f"Loaded {len(geojson['features'])} intersections from cache")
                return geojson
        except Exception:
            pass

    # Fetch or simulate
    if settings.simulation_mode:
        logger.info("Simulation mode — generating fake intersections")
        geojson = _generate_simulated_intersections(30)
    else:
        geojson = await _fetch_from_overpass()
        if not geojson:
            logger.warning("Overpass failed — falling back to simulated data")
            geojson = _generate_simulated_intersections(30)

    # Cache to disk
    GEOJSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GEOJSON_PATH, "w") as f:
        json.dump(geojson, f, indent=2)
    logger.info(f"Saved {len(geojson['features'])} intersections to {GEOJSON_PATH}")

    return geojson


def get_intersection_coords(geojson: dict) -> list[dict]:
    """Extract intersection list from GeoJSON for fetchers."""
    results = []
    for feat in geojson.get("features", []):
        props = feat["properties"]
        coords = feat["geometry"]["coordinates"]
        results.append({
            "id": props["id"],
            "name": props.get("name", "Unknown"),
            "lat": coords[1],
            "lng": coords[0],
            "road_names": props.get("road_names", []),
            "num_lanes": props.get("num_lanes", 2),
            "speed_limit_kmh": props.get("speed_limit_kmh", 50),
            "zone": props.get("zone", "general"),
            "osm_node_id": props.get("osm_node_id"),
        })
    return results
