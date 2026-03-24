from sqlalchemy.orm import Session
from datetime import datetime, timezone
from ..models.all_models import Signal, SOSEvent
from ..schemas.all_schemas import TelemetryData
from ..core.websocket_manager import manager
from ..services.pulse_service import pulse_service

class TelemetryService:
    @staticmethod
    def _to_utc_now():
        return datetime.now(timezone.utc)

    async def process_telemetry(self, db: Session, data: TelemetryData) -> dict:
        timestamp = data.timestamp or self._to_utc_now()

        signal = Signal(
            device_id=data.device_id,
            latitude=data.latitude,
            longitude=data.longitude,
            pulse=data.pulse,
            battery=data.battery,
            sos=data.sos,
            received_at=timestamp,
        )
        db.add(signal)
        db.flush()

        await pulse_service.validate_pulse(db, data)

        active_event = (
            db.query(SOSEvent)
            .filter(SOSEvent.device_id == data.device_id, SOSEvent.is_active.is_(True))
            .order_by(SOSEvent.started_at.desc())
            .first()
        )
        event_type = "telemetry_update"
        event_id = active_event.id if active_event else None

        if data.sos:
            if not active_event:
                active_event = SOSEvent(
                    device_id=data.device_id,
                    is_active=True,
                    started_at=timestamp,
                    last_latitude=data.latitude,
                    last_longitude=data.longitude,
                    last_pulse=data.pulse,
                )
                db.add(active_event)
                db.flush()
                event_type = "sos_alert"
            else:
                active_event.last_latitude = data.latitude
                active_event.last_longitude = data.longitude
                active_event.last_pulse = data.pulse
            event_id = active_event.id
        else:
            if active_event:
                active_event.is_active = False
                active_event.resolved_at = timestamp
                active_event.last_latitude = data.latitude
                active_event.last_longitude = data.longitude
                active_event.last_pulse = data.pulse
                event_id = active_event.id

        db.commit()

        payload = {
            "type": event_type,
            "event_id": event_id,
            "device_id": data.device_id,
            "latitude": data.latitude,
            "longitude": data.longitude,
            "pulse": data.pulse,
            "battery": data.battery,
            "sos": data.sos,
            "timestamp": timestamp.isoformat(),
        }
        await manager.broadcast(payload)
        return payload

telemetry_service = TelemetryService()
