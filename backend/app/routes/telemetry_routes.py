import json
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.all_schemas import TelemetryData, DeviceStatus, EncryptedTelemetry
from ..models.all_models import Signal, SOSEvent
from ..services.telemetry_service import telemetry_service
from ..config import settings
from ..core.security import decrypt_aes_256_cbc_json

router = APIRouter()

def verify_device_key(x_device_key: str = Header(..., alias="X-Device-Key")):
    if x_device_key != settings.DEVICE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid Device API Key")

@router.get("/devices/status", response_model=List[DeviceStatus])
def get_devices_status(db: Session = Depends(get_db)):
    latest_per_device = {}
    rows = db.query(Signal).order_by(Signal.received_at.desc()).limit(5000).all()
    for row in rows:
        if row.device_id not in latest_per_device:
            latest_per_device[row.device_id] = row

    statuses = []
    now = datetime.now(timezone.utc)
    for device_id, signal in latest_per_device.items():
        active_event = (
            db.query(SOSEvent)
            .filter(SOSEvent.device_id == device_id, SOSEvent.is_active.is_(True))
            .first()
        )
        delta = now - signal.received_at.replace(tzinfo=timezone.utc)
        statuses.append(
            DeviceStatus(
                device_id=device_id,
                is_online=delta.total_seconds() <= 30,
                last_seen=signal.received_at,
                last_latitude=signal.latitude,
                last_longitude=signal.longitude,
                last_pulse=signal.pulse,
                sos_active=bool(active_event),
            )
        )
    return statuses

@router.post("/telemetry/secure", dependencies=[Depends(verify_device_key)])
async def post_secure_telemetry(payload: EncryptedTelemetry, db: Session = Depends(get_db)):
    decrypted_json = decrypt_aes_256_cbc_json(payload.encrypted_data, aes_key=payload.aes_key)
    if decrypted_json is None:
        try:
            decrypted_json = json.loads(payload.encrypted_data)
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Could not decrypt/parse secure payload") from exc

    if payload.device_id and not decrypted_json.get("device_id"):
        decrypted_json["device_id"] = payload.device_id
    data = TelemetryData(**decrypted_json)
    ws_payload = await telemetry_service.process_telemetry(db, data)
    return {"success": True, "event_id": ws_payload.get("event_id"), "stored_at": ws_payload["timestamp"]}

@router.post("/telemetry", dependencies=[Depends(verify_device_key)])
async def post_telemetry(data: TelemetryData, db: Session = Depends(get_db)):
    ws_payload = await telemetry_service.process_telemetry(db, data)
    return {"success": True, "event_id": ws_payload.get("event_id"), "stored_at": ws_payload["timestamp"]}
