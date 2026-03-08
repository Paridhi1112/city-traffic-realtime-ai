"""
Urban Traffic Brain — FastAPI Application Entry Point
=====================================================
Full application with all routes, WebSocket, scheduler, and lifecycle management.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from config import get_settings
from db.redis_manager import get_redis, close_redis, RedisStateManager
from api.websocket import websocket_endpoint, broadcast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()

# Store intersections globally after loading
_intersections: list[dict] = []


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    global _intersections
    logger.info("=" * 60)
    logger.info("  Urban Traffic Brain — Starting Up")
    logger.info(f"  City: {settings.city_name}")
    logger.info(f"  Simulation Mode: {settings.simulation_mode}")
    logger.info("=" * 60)

    # 1. Initialize database
    try:
        from db.init_db import init_database
        await init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Database init failed: {e}")

    # 2. Load intersections from OSM / simulation
    try:
        from data_fetchers.osm_loader import load_intersections, get_intersection_coords
        geojson = await load_intersections()
        _intersections = get_intersection_coords(geojson)
        logger.info(f"Loaded {len(_intersections)} intersections")

        # Seed intersections to DB
        await _seed_intersections(_intersections)
    except Exception as e:
        logger.error(f"Failed to load intersections: {e}")

    # 3. Build city graph
    try:
        from city_graph.graph_builder import build_graph
        graph = build_graph(_intersections)
        logger.info(f"City graph built: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")
    except Exception as e:
        logger.warning(f"Graph build failed: {e}")

    # 4. Load ML models
    try:
        from prediction_engine.congestion_model import load_models
        load_models()
    except Exception as e:
        logger.warning(f"ML models not loaded: {e}")

    # 5. Start scheduler
    try:
        from scheduler.polling_scheduler import setup_scheduler
        from scheduler.jobs import set_ws_broadcast
        set_ws_broadcast(broadcast)
        setup_scheduler(_intersections)
        logger.info("Scheduler started")
    except Exception as e:
        logger.error(f"Scheduler failed to start: {e}")

    # 6. Run initial data fetch
    try:
        from data_fetchers.data_aggregator import aggregate_all_data
        if _intersections:
            await aggregate_all_data(_intersections)
            logger.info("Initial data fetch complete")
    except Exception as e:
        logger.warning(f"Initial data fetch failed: {e}")

    logger.info("Urban Traffic Brain is LIVE")
    yield

    # Shutdown
    logger.info("Shutting down Urban Traffic Brain...")
    try:
        from scheduler.polling_scheduler import shutdown_scheduler
        shutdown_scheduler()
    except Exception:
        pass
    await close_redis()
    logger.info("Shutdown complete")


async def reload_city_context(new_city: str, new_bbox: str):
    """
    Dynamically change the active city and restart all background processes
    without taking the FastAPI server down.
    """
    global _intersections
    settings.update_city(new_city, new_bbox)
    
    logger.info("=" * 60)
    logger.info(f"  Dynamic City Switch Initiated: {new_city}")
    logger.info("=" * 60)

    # 1. Shutdown existing scheduler jobs cleanly
    try:
        from scheduler.polling_scheduler import shutdown_scheduler, setup_scheduler
        shutdown_scheduler()
    except Exception as e:
        logger.warning(f"Failed to shutdown scheduler: {e}")

    # 2. Reload intersections for the new bounding box
    try:
        from data_fetchers.osm_loader import load_intersections, get_intersection_coords
        from data_fetchers.osm_loader import GEOJSON_PATH
        import os
        
        # force bust the file cache
        if GEOJSON_PATH.exists():
            os.remove(GEOJSON_PATH)

        geojson = await load_intersections()
        _intersections = get_intersection_coords(geojson)
        logger.info(f"Dynamically loaded {len(_intersections)} intersections for {new_city}")

        # Seed new intersections to DB
        await _seed_intersections(_intersections)
    except Exception as e:
        logger.error(f"Failed to load new intersections: {e}")

    # 3. Rebuild city graph
    try:
        from city_graph.graph_builder import build_graph
        graph = build_graph(_intersections)
        logger.info(f"New city graph built: {graph.number_of_nodes()} nodes")
    except Exception as e:
        logger.warning(f"New graph build failed: {e}")

    # 4. Restart Scheduler + trigger manual refresh
    try:
        from scheduler.jobs import set_ws_broadcast
        set_ws_broadcast(broadcast)
        setup_scheduler(_intersections)
        logger.info("Scheduler restarted with new city bounds")
        
        from data_fetchers.data_aggregator import aggregate_all_data
        if _intersections:
            await aggregate_all_data(_intersections)
            logger.info("Forced initial data fetch for new city complete")
            
    except Exception as e:
        logger.error(f"Failed to restart background jobs for new city: {e}")



async def _seed_intersections(intersections: list[dict]):
    """Seed intersection data to database."""
    try:
        from db.database import async_session_factory
        from models.intersection import Intersection
        from sqlalchemy import select, func
        import uuid

        async with async_session_factory() as session:
            count = (await session.execute(select(func.count()).select_from(Intersection))).scalar()
            if count and count > 0:
                return  # Already seeded

            for inter in intersections:
                db_inter = Intersection(
                    id=inter["id"] if isinstance(inter["id"], uuid.UUID) else uuid.UUID(inter["id"]) if len(str(inter["id"])) == 36 else uuid.uuid4(),
                    name=inter.get("name", "Unknown"),
                    lat=inter["lat"],
                    lng=inter["lng"],
                    road_names=inter.get("road_names", []),
                    num_lanes=inter.get("num_lanes", 2),
                    speed_limit_kmh=inter.get("speed_limit_kmh", 50),
                    zone=inter.get("zone", "general"),
                    osm_node_id=inter.get("osm_node_id"),
                )
                session.add(db_inter)
            await session.commit()
            logger.info(f"Seeded {len(intersections)} intersections to DB")
    except Exception as e:
        logger.error(f"Failed to seed intersections: {e}")


# ── Create App ──
app = FastAPI(
    title="Urban Traffic Brain",
    description="AI-powered city-wide traffic management system",
    version="0.2.0",
    lifespan=lifespan,
)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Include API Routers ──
from api.routes.traffic import router as traffic_router
from api.routes.decisions import router as decisions_router
from api.routes.intersections import router as intersections_router
from api.routes.events import router as events_router
from api.routes.emissions import router as emissions_router
from api.routes.alerts import router as alerts_router

app.include_router(traffic_router)
app.include_router(decisions_router)
app.include_router(intersections_router)
app.include_router(events_router)
app.include_router(emissions_router)
app.include_router(alerts_router)

# ── WebSocket ──
app.websocket("/ws/traffic")(websocket_endpoint)


# ── Health + Status Endpoints ──
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "urban-traffic-brain-backend",
        "city": settings.city_name,
        "simulation_mode": settings.simulation_mode,
        "intersections_loaded": len(_intersections),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/datasources/status")
async def datasources_status():
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        status = await rsm.get_datasource_status()
        if status:
            return status
    except Exception:
        pass
    return {
        "tomtom": {"status": "not_configured"},
        "here": {"status": "not_configured"},
        "open_meteo": {"status": "not_configured"},
        "ticketmaster": {"status": "not_configured"},
        "overpass_api": {"status": "not_configured"},
        "gtfs": {"status": "not_configured"},
    }


@app.get("/api/weather/current")
async def get_weather():
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        weather = await rsm.get_weather()
        return weather or {"condition": "Unknown"}
    except Exception:
        return {"condition": "Unknown"}


@app.get("/api/predictions/{intersection_id}")
async def get_predictions(intersection_id: str):
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        pred = await rsm.get_prediction(intersection_id)
        return pred or {"error": "No prediction available"}
    except Exception:
        return {"error": "Prediction unavailable"}


@app.get("/api/incidents/active")
async def get_active_incidents():
    try:
        r = await get_redis()
        rsm = RedisStateManager(r)
        state = await rsm.get_city_state()
        if state:
            incidents = []
            for i in state.get("intersections", []):
                incidents.extend(i.get("active_incidents", []))
            return {"incidents": incidents}
    except Exception:
        pass
    return {"incidents": []}


if __name__ == "__main__":
    import uvicorn
    import os
    
    # Run the server
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
