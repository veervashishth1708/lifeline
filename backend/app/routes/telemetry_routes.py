from fastapi import APIRouter, Depends, HTTPException, Header
import traceback
import json
import httpx
import asyncio
from typing import List
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.all_schemas import TelemetryData, DeviceStatus, EncryptedTelemetry
from ..models.all_models import Device
from ..services.telemetry_service import telemetry_service
from ..config import settings
from ..core.security import decrypt_aes_256_cbc_raw

router = APIRouter()

def verify_device_key(x_device_key: str = Header(...)):
    if x_device_key != settings.DEVICE_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid Device API Key")

@router.get("/devices/status", response_model=List[DeviceStatus])
def get_devices_status(db: Session = Depends(get_db)):
    """
    Get the status of all registered devices.
    """
    return db.query(Device).all()

# Node mapping for E2EE payloads 
NODE_COORDS = {
    "Node-A": {"lat": 29.211372, "lon": 77.017304},
    "Node-B": {"lat": 29.210347, "lon": 77.015948},
    "Node-C": {"lat": 29.21141446472551, "lon": 77.01605426676902}
}

async def send_to_decoder_monitor(encrypted: str, decrypted: str):
    """Sends payload details to the UI monitor on port 8001."""
    try:
        async with httpx.AsyncClient() as client:
            await client.post("http://localhost:8001/decoder-update", json={
                "encrypted_data": encrypted,
                "decrypted_data": decrypted,
                "aes_key": settings.AES_KEY
            }, timeout=2)
    except Exception as e:
        print(f"Decoder Monitor not running on 8001: {e}")

@router.post("/telemetry/secure", dependencies=[Depends(verify_device_key)])
async def post_secure_telemetry(payload: EncryptedTelemetry, db: Session = Depends(get_db)):
    """
    Encrypted endpoint for Midway Panel to post secured telemetry.
    Supports JSON or E2EE Raw String payloads.
    """
    try:
        decrypted_raw = decrypt_aes_256_cbc_raw(payload.encrypted_data)
        if not decrypted_raw:
            raise HTTPException(status_code=400, detail="Decryption Failed")
        
        # Determine payload type
        decrypted_raw = decrypted_raw.strip()
        
        # Async send decryption log to the new decoding monitor on port 8001
        asyncio.create_task(send_to_decoder_monitor(payload.encrypted_data, decrypted_raw))
        
        telemetry_dict = {}
        is_sos_response = False
        is_cp_response = False
        
        if decrypted_raw.startswith("{"):
            # Old JSON method
            telemetry_dict = json.loads(decrypted_raw)
        else:
            # E2EE Raw String method from Node
            # E.g., "SOS", "Node-A", "CP:user:Node-A"
            target_id = "midway_panel"
            lat = 30.6862
            lon = 76.6619
            is_sos = False
            is_checkpoint = False
            user_id = ""
            
            if decrypted_raw.startswith("CP:"):
                parts = decrypted_raw.split(":")
                if len(parts) >= 3:
                    is_checkpoint = True
                    user_id = parts[1]
                    target_id = parts[2]
                    is_cp_response = True
            elif decrypted_raw == "SOS":
                is_sos = True
                is_sos_response = True
            else:
                # E.g. "Node-A"
                is_sos = True
                target_id = decrypted_raw
                is_sos_response = True
            
            if target_id in NODE_COORDS:
                lat = NODE_COORDS[target_id]["lat"]
                lon = NODE_COORDS[target_id]["lon"]
                
            telemetry_dict = {
                "device_id": target_id,
                "latitude": lat,
                "longitude": lon,
                "pulse": 72,
                "sos": is_sos,
                "is_checkpoint": is_checkpoint,
                "user_id": user_id
            }

        # Manually validate against TelemetryData
        data = TelemetryData(**telemetry_dict)
        
        device = await telemetry_service.process_telemetry(db, data)
        return {
            "status": "success", 
            "device_id": device.id,
            "is_sos": is_sos_response,
            "is_checkpoint": is_cp_response
        }
    except Exception as e:
        print(f"SECURE TELEMETRY ERROR: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/telemetry", dependencies=[Depends(verify_device_key)])
async def post_telemetry(data: TelemetryData, db: Session = Depends(get_db)):
    """
    Endpoint for devices to post GPS and Pulse telemetry.
    Supports real-time broadcasting and SOS state management.
    """
    try:
        device = await telemetry_service.process_telemetry(db, data)
        return {"status": "success", "device_id": device.id}
    except Exception as e:
        print("CRITICAL ERROR IN TELEMETRY:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
