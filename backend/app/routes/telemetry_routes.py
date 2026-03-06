from fastapi import APIRouter, Depends, HTTPException, Header
import traceback
from typing import List
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.all_schemas import TelemetryData, DeviceStatus
from ..models.all_models import Device
from ..services.telemetry_service import telemetry_service
from ..config import settings

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
