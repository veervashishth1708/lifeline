from sqlalchemy.orm import Session
from ..models.all_models import PulseData, Device
from ..schemas.all_schemas import TelemetryData
from ..core.websocket_manager import manager
from ..services.n8n_service import n8n_service
import asyncio

class PulseService:
    @staticmethod
    async def validate_pulse(db: Session, data: TelemetryData):
        """
        Logic to check for abnormal pulse:
        - Range: 60-100 BPM
        - Fluctuation check: Sudden jump > 20 BPM from last reading
        """
        is_abnormal = False
        alert_type = "normal"
        reason = ""

        # 1. Check for sudden jump
        last_reading = db.query(PulseData).filter(
            PulseData.device_id == data.device_id
        ).order_by(PulseData.timestamp.desc()).offset(1).first()

        if last_reading:
            diff = abs(data.pulse - last_reading.bpm)
            if diff > 20:
                is_abnormal = True
                alert_type = "critical"
                reason = f"Critical Pulse Fluctuation (+{diff} BPM)"

        # 2. Check absolute ranges
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
                "timestamp": data.timestamp.isoformat()
            })
            
            # If critical, also trigger n8n
            if alert_type == "critical":
                asyncio.create_task(n8n_service.trigger_sos_webhook({
                    "device_id": data.device_id,
                    "location": None, # Will be filled by caller or fetched
                    "pulse": data.pulse,
                    "timestamp": data.timestamp.isoformat(),
                    "severity_level": "critical_pulse"
                }))
            
        return is_abnormal

pulse_service = PulseService()
