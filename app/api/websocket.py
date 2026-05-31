"""WebSocket manager for real-time updates."""

import asyncio
import json
import logging
from typing import Dict, Set, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        self._connections: Dict[int, Set[WebSocket]] = {}
        self._admin_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, user_id: Optional[int] = None) -> None:
        """Accept WebSocket connection."""
        await websocket.accept()

        if user_id:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(websocket)
            logger.info(f"User {user_id} connected, total: {len(self._connections[user_id])}")
        else:
            self._admin_connections.add(websocket)
            logger.info(f"Admin connected, total admins: {len(self._admin_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: Optional[int] = None) -> None:
        """Remove WebSocket connection."""
        if user_id and user_id in self._connections:
            self._connections[user_id].discard(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]
            logger.info(f"User {user_id} disconnected")

        self._admin_connections.discard(websocket)
        logger.info("Admin disconnected")

    async def send_personal(self, message: dict, user_id: int) -> None:
        """Send message to specific user."""
        if user_id not in self._connections:
            return

        message_json = json.dumps(message)
        dead_connections = set()

        for websocket in self._connections[user_id]:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(message_json)
                else:
                    dead_connections.add(websocket)
            except Exception as e:
                logger.error(f"Error sending to user {user_id}: {e}")
                dead_connections.add(websocket)

        for dead in dead_connections:
            self._connections[user_id].discard(dead)

    async def send_admin(self, message: dict) -> None:
        """Send message to all admins."""
        message_json = json.dumps(message)
        dead_connections = set()

        for websocket in self._admin_connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(message_json)
                else:
                    dead_connections.add(websocket)
            except Exception as e:
                logger.error(f"Error sending to admin: {e}")
                dead_connections.add(websocket)

        for dead in dead_connections:
            self._admin_connections.discard(dead)

    async def broadcast(self, message: dict) -> None:
        """Broadcast message to all connected users."""
        message_json = json.dumps(message)

        all_connections: Set[WebSocket] = set()
        for connections in self._connections.values():
            all_connections.update(connections)
        all_connections.update(self._admin_connections)

        dead_connections = set()

        for websocket in all_connections:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(message_json)
                else:
                    dead_connections.add(websocket)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                dead_connections.add(websocket)

        for dead in dead_connections:
            for user_id in self._connections:
                self._connections[user_id].discard(dead)
            self._admin_connections.discard(dead)

    def get_connected_users(self) -> list[int]:
        """Get list of connected user IDs."""
        return list(self._connections.keys())

    def get_connection_count(self) -> int:
        """Get total connection count."""
        return sum(len(connections) for connections in self._connections.values())


manager = ConnectionManager()

ws_router = APIRouter()


@ws_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates."""
    user_id: Optional[int] = None
    is_admin = False

    try:
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                msg_type = message.get("type")

                if msg_type == "auth":
                    user_id = message.get("user_id")
                    is_admin = message.get("is_admin", False)

                    if is_admin:
                        await manager.connect(websocket)
                    else:
                        await manager.connect(websocket, user_id)

                    await manager.send_personal(
                        {"type": "auth_confirmed", "user_id": user_id},
                        user_id,
                    )

                elif msg_type == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

                elif msg_type == "subscribe":
                    channel = message.get("channel")
                    if channel == "trades":
                        logger.info(f"User {user_id} subscribed to trades")

                elif msg_type == "unsubscribe":
                    channel = message.get("channel")
                    if channel == "trades":
                        logger.info(f"User {user_id} unsubscribed from trades")

            except json.JSONDecodeError:
                logger.warning("Received invalid JSON")
                await websocket.send_text(
                    json.dumps({"type": "error", "message": "Invalid JSON"})
                )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: user_id={user_id}")
        manager.disconnect(websocket, user_id)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


async def notify_trade_update(user_id: int, trade_data: dict) -> None:
    """Notify user about trade update."""
    await manager.send_personal(
        {
            "type": "trade_update",
            "status": trade_data.get("status"),
            "message": trade_data.get("message"),
            "trade_id": trade_data.get("trade_id"),
            "timestamp": trade_data.get("timestamp"),
        },
        user_id,
    )


async def notify_payment_update(user_id: int, payment_data: dict) -> None:
    """Notify user about payment update."""
    await manager.send_personal(
        {
            "type": "payment_update",
            "status": payment_data.get("status"),
            "message": payment_data.get("message"),
            "payment_id": payment_data.get("payment_id"),
            "timestamp": payment_data.get("timestamp"),
        },
        user_id,
    )


async def notify_subscription_update(user_id: int, sub_data: dict) -> None:
    """Notify user about subscription update."""
    await manager.send_personal(
        {
            "type": "subscription_update",
            "status": sub_data.get("status"),
            "message": sub_data.get("message"),
            "expiry_date": sub_data.get("expiry_date"),
            "timestamp": sub_data.get("timestamp"),
        },
        user_id,
    )


async def broadcast_alert(alert_data: dict) -> None:
    """Broadcast alert to all users."""
    await manager.send_admin(
        {
            "type": "alert",
            "severity": alert_data.get("severity"),
            "message": alert_data.get("message"),
            "timestamp": alert_data.get("timestamp"),
        }
    )


async def notify_price_alert(user_id: int, price_data: dict) -> None:
    """Notify user about price alert."""
    await manager.send_personal(
        {
            "type": "price_alert",
            "token": price_data.get("token"),
            "price": price_data.get("price"),
            "direction": price_data.get("direction"),
            "timestamp": price_data.get("timestamp"),
        },
        user_id,
    )
