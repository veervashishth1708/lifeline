from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from datetime import datetime, timezone
from ..models.all_models import SOSEvent
from ..schemas.all_schemas import SOSActiveResponse
from typing import List

router = APIRouter()

@router.get("/sos/active", response_model=List[SOSActiveResponse])
def get_active_sos(db: Session = Depends(get_db)):
    events = (
        db.query(SOSEvent)
        .filter(SOSEvent.is_active.is_(True))
        .order_by(SOSEvent.started_at.desc())
        .all()
    )
    response = []
    for event in events:
        response.append(
            SOSActiveResponse(
                id=event.id,
                device_id=event.device_id,
                is_active=event.is_active,
                started_at=event.started_at,
                pulse_data=[{"bpm": event.last_pulse, "timestamp": event.started_at.isoformat()}],
                location_data=[
                    {
                        "latitude": event.last_latitude,
                        "longitude": event.last_longitude,
                        "timestamp": event.started_at.isoformat(),
                    }
                ],
            )
        )
    return response

@router.post("/sos/resolve/{event_id}")
def resolve_sos(event_id: int, db: Session = Depends(get_db)):
    event = db.query(SOSEvent).filter(SOSEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="SOS Event not found")

    event.is_active = False
    event.resolved_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "event_id": event_id, "status": "resolved"}
