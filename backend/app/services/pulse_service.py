from sqlalchemy.orm import Session
from ..models.all_models import Signal
from ..schemas.all_schemas import TelemetryData
from ..core.websocket_manager import manager

class PulseService:
    @staticmethod
    async def validate_pulse(db: Session, data: TelemetryData):
        if data.pulse is None:
            return False

        is_abnormal = False
        alert_type = "normal"
        reason = ""

        last_reading = (
            db.query(Signal)
            .filter(Signal.device_id == data.device_id, Signal.pulse.is_not(None))
            .order_by(Signal.received_at.desc())
            .first()
        )

        if last_reading and last_reading.pulse is not None:
            diff = abs(data.pulse - last_reading.pulse)
            if diff > 20:
                is_abnormal = True
                alert_type = "critical"
                reason = f"Critical Pulse Fluctuation (+{diff} BPM)"

        if not is_abnormal:
            if data.pulse > 100:
                is_abnormal = True
                alert_type = "high_pulse"
                reason = "High Pulse (Tachycardia)"
            elif data.pulse < 60:
                is_abnormal = True
                alert_type = "low_pulse"
                reason = "Low Pulse (Bradycardia)"

        if is_abnormal:
            # Broadcast abnormal pulse event
            await manager.broadcast({
                "type": "pulse_alert",
                "device_id": data.device_id,
                "pulse": data.pulse,
                "alert_level": alert_type,
                "reason": reason,
                "timestamp": (data.timestamp.isoformat() if data.timestamp else None)
            })
            
        return is_abnormal

pulse_service = PulseService()
