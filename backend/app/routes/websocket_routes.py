from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from ..core.websocket_manager import manager
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/ws/sos")
async def websocket_sos_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and listen for any client messages
            data = await websocket.receive_text()
            # Handle specific client requests if any
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@router.websocket("/ws/telemetry/{device_id}")
async def websocket_telemetry_endpoint(websocket: WebSocket, device_id: str):
    await manager.connect(websocket)
    manager.subscribe_to_device(device_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
