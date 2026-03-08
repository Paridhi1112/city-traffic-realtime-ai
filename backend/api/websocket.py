"""
WebSocket endpoint for live traffic updates.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Set

from fastapi import WebSocket, WebSocketDisconnect
from db.redis_manager import get_redis, RedisStateManager

logger = logging.getLogger(__name__)

# Active WebSocket connections
_connections: Set[WebSocket] = set()


async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections for live updates."""
    await websocket.accept()
    _connections.add(websocket)
    logger.info(f"WebSocket client connected. Total: {len(_connections)}")

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Urban Traffic Brain",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        # Fetch and send immediate initial state
        try:
            r = await get_redis()
            rsm = RedisStateManager(r)
            state = await rsm.get_city_state()
            if state:
                await websocket.send_text(json.dumps({
                    "type": "city_state_update",
                    "data": state,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }, default=str))
        except Exception as e:
            logger.error(f"Failed to send initial city state: {e}")

        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Handle client ping/pong
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        _connections.discard(websocket)


async def broadcast(message: dict):
    """Broadcast message to all connected WebSocket clients."""
    global _connections
    if not _connections:
        return

    dead = set()
    payload = json.dumps(message, default=str)

    for ws in _connections.copy():
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)

    _connections -= dead
    if dead:
        logger.info(f"Removed {len(dead)} dead WebSocket connections")
