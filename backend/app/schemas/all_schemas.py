from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# Auth Schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    role: str
    class Config:
        from_attributes = True

# Device & Telemetry Schemas
class TelemetryData(BaseModel):
    device_id: str
    latitude: float
    longitude: float
    pulse: int
    sos: bool
    is_checkpoint: Optional[bool] = False
    user_id: Optional[str] = None
    timestamp: Optional[datetime] = None # Make optional for robust hardware ingestion

class DeviceStatus(BaseModel):
    id: str
    sos_active: bool
    last_seen: Optional[datetime]
    class Config:
        from_attributes = True

# SOS Event Schemas
class SOSRequest(BaseModel):
    device_id: str

class SOSEventSchema(BaseModel):
    id: int
    device_id: str
    start_time: datetime
    end_time: Optional[datetime]
    status: str
    class Config:
        from_attributes = True

# Pulse & Location History
class PulseHistory(BaseModel):
    bpm: int
    timestamp: datetime
    class Config:
        from_attributes = True
