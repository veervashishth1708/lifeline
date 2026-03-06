from sqlalchemy.orm import Session
from ..models.all_models import Device, PulseData, LocationData, SOSEvent
from ..schemas.all_schemas import TelemetryData
from ..core.websocket_manager import manager
from ..services.n8n_service import n8n_service
from ..services.pulse_service import pulse_service
from datetime import datetime
import asyncio

class TelemetryService:
    async def process_telemetry(self, db: Session, data: TelemetryData):
        print(f"DEBUG: Processing Telemetry for device={data.device_id}, sos={data.sos}, pulse={data.pulse}, lat={data.latitude}, lng={data.longitude}")
        
        # Default timestamp if missing
        if not data.timestamp:
            data.timestamp = datetime.now()

        # 1. Update Device status
        device = db.query(Device).filter(Device.id == data.device_id).first()
        if not device:
            print(f"DEBUG: Creating new device entry for {data.device_id}")
            device = Device(id=data.device_id)
            db.add(device)
            db.commit()
            db.refresh(device)
        
        device.last_seen = data.timestamp
        
        # 3. Store Pulse Data
        pulse_entry = PulseData(device_id=data.device_id, bpm=data.pulse, timestamp=data.timestamp)
        db.add(pulse_entry)
        
        # Validate Pulse
        await pulse_service.validate_pulse(db, data)

        # 4. Store Location Data
        loc_entry = LocationData(device_id=data.device_id, latitude=data.latitude, longitude=data.longitude, timestamp=data.timestamp)
        db.add(loc_entry)

        db.commit()

        # 5. Broadcast via WebSocket (DEFERRED to end for speed)
        # Removed redundant broadcast block

        active_sos_id = None
        
        # 2. Handle SOS state (database update)
        if data.sos:
            # Check if we should create a NEW event (cooldown of 5 seconds to avoid spam)
            recent_event = db.query(SOSEvent).filter(
                SOSEvent.device_id == data.device_id,
                SOSEvent.status == "active"
            ).order_by(SOSEvent.start_time.desc()).first()
            
            # If no active event or the active one is old (allowing multiple "pulls" if they want)
            # Actually, the user says "new sos pulled every time". I'll create one if the state is true.
            # To avoid spam, I'll only create one if the most recent one is older than 2 seconds.
            if not recent_event or (datetime.now() - recent_event.start_time.replace(tzinfo=None)).total_seconds() > 2:
                print(f"DEBUG: TRIGGERING NEW SOS EVENT for {data.device_id}")
                device.sos_active = True
                new_event = SOSEvent(device_id=data.device_id, status="active")
                db.add(new_event)
                db.commit() # Save to get ID
                db.refresh(new_event)
                active_sos_id = new_event.id
                
                # 6. Trigger n8n
                asyncio.create_task(n8n_service.trigger_sos_webhook({
                    "event_id": active_sos_id,
                    "device_id": data.device_id,
                    "location": {"lat": data.latitude, "lng": data.longitude},
                    "pulse": data.pulse,
                    "timestamp": data.timestamp.isoformat(),
                    "severity_level": "emergency"
                }))
            else:
                active_sos_id = recent_event.id
        elif not data.sos and device.sos_active:
            print(f"DEBUG: RESOLVING SOS EVENT for {data.device_id}")
            device.sos_active = False
            active_events = db.query(SOSEvent).filter(
                SOSEvent.device_id == data.device_id, 
                SOSEvent.status == "active"
            ).all()
            for event in active_events:
                event.status = "resolved"
                event.end_time = datetime.now()
            db.commit()

        # 5. Broadcast via WebSocket (Include event_id)
        if data.is_checkpoint:
            print(f"DEBUG: Broadcasting checkpoint_reached for {data.device_id}")
            await manager.broadcast({
                "type": "checkpoint_reached",
                "device_id": data.device_id,
                "user_id": data.user_id,
                "latitude": data.latitude,
                "longitude": data.longitude,
                "timestamp": data.timestamp.isoformat()
            })
        else:
            print(f"DEBUG: Broadcasting {'sos_alert' if data.sos else 'telemetry_update'} for {data.device_id}")
            await manager.broadcast({
                "type": "sos_alert" if data.sos else "telemetry_update",
                "event_id": active_sos_id,
                "device_id": data.device_id,
                "latitude": data.latitude,
                "longitude": data.longitude,
                "pulse": data.pulse,
                "sos": data.sos,
                "timestamp": data.timestamp.isoformat()
            })

        db.commit()
        print(f"DEBUG: Telemetry processed successfully for {data.device_id}")
        return device

telemetry_service = TelemetryService()
