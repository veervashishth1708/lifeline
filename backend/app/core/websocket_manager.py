import json
import asyncio
import redis.asyncio as redis
from typing import Dict, List
from fastapi import WebSocket
from ..config import settings

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.device_subscriptions: Dict[str, List[WebSocket]] = {}
        self.redis_client = None
        self.pubsub = None
        self._redis_available = False
        
        try:
            # Quick check if Redis is even reachable
            self.redis_client = redis.from_url(
                settings.REDIS_URL, 
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1
            )
            self._redis_available = True
        except Exception as e:
            print(f"Warning: Redis not reachable at {settings.REDIS_URL}. Falling back to local mode. Error: {e}")
            self.redis_client = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Start listener if Redis is supposed to be active but not listening yet
        if self._redis_available and not self.pubsub:
            asyncio.create_task(self._start_redis_listener())

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        for subs in self.device_subscriptions.values():
            if websocket in subs:
                subs.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message locally and via Redis if available"""
        msg_str = json.dumps(message)
        
        # 1. Local Broadcast (Fast & Reliable)
        for connection in self.active_connections[:]: # Iterate over a copy to avoid removal errors
            try:
                await connection.send_text(msg_str)
            except Exception as e:
                print(f"DEBUG: WebSocket send failed, disconnecting: {e}")
                self.disconnect(connection)

        # 2. Redis Broadcast (Optional for scale)
        if self._redis_available and self.redis_client:
            try:
                # Use a timeout to prevent hanging if Redis becomes unresponsive
                await asyncio.wait_for(
                    self.redis_client.publish("antigravity_events", msg_str),
                    timeout=0.5
                )
            except Exception as e:
                print(f"Redis publish failed: {e}. Disabling Redis publishing until re-init.")
                self._redis_available = False

    async def _start_redis_listener(self):
        """Background task to listen to Redis and send to local clients"""
        if not self._redis_available or not self.redis_client:
            return

        try:
            self.pubsub = self.redis_client.pubsub()
            await self.pubsub.subscribe("antigravity_events")
            
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    # Only broadcast if it didn't come from this instance (if we had instance IDs)
                    # For now, we trust local broadcast and use Redis for other instances
                    # but avoid double-delivery on local instance if redundant
                    pass 
        except Exception as e:
            print(f"Redis listener error: {e}")
            self._redis_available = False

    def subscribe_to_device(self, device_id: str, websocket: WebSocket):
        if device_id not in self.device_subscriptions:
            self.device_subscriptions[device_id] = []
        if websocket not in self.device_subscriptions[device_id]:
            self.device_subscriptions[device_id].append(websocket)

manager = ConnectionManager()
