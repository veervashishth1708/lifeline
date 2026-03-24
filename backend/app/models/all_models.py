from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, func
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Signal(Base):
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    pulse = Column(Integer, nullable=True)
    battery = Column(Integer, nullable=True)
    sos = Column(Boolean, nullable=False, default=False)
    received_at = Column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)


class SOSEvent(Base):
    __tablename__ = "sos_events"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, index=True, nullable=False)
    is_active = Column(Boolean, index=True, default=True, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    last_latitude = Column(Float, nullable=False)
    last_longitude = Column(Float, nullable=False)
    last_pulse = Column(Integer, nullable=True)
