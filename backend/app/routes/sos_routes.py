from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.all_models import Device, SOSEvent
from ..schemas.all_schemas import SOSRequest, SOSEventSchema
from typing import List

router = APIRouter()

@router.get("/sos/active", response_model=List[SOSEventSchema])
def get_active_sos(db: Session = Depends(get_db)):
    return db.query(SOSEvent).filter(SOSEvent.status == "active").all()

@router.post("/sos/resolve/{event_id}")
def resolve_sos(event_id: int, db: Session = Depends(get_db)):
    event = db.query(SOSEvent).filter(SOSEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="SOS Event not found")
    
    event.status = "resolved"
    # Also update device status
    device = db.query(Device).filter(Device.id == event.device_id).first()
    if device:
        device.sos_active = False
        
    db.commit()
    return {"status": "resolved"}
