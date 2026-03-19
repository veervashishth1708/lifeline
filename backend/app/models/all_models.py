from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="operator")

    devices = relationship("Device", back_populates="owner")

class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True, index=True) # Device Serial/ID
    user_id = Column(Integer, ForeignKey("users.id"))
    last_seen = Column(DateTime(timezone=True), onupdate=func.now())
    sos_active = Column(Boolean, default=False)
    last_pulse = Column(Integer, nullable=True)
    last_lat = Column(Float, nullable=True)
    last_lng = Column(Float, nullable=True)

    owner = relationship("User", back_populates="devices")
    events = relationship("SOSEvent", back_populates="device")
    pulse_history = relationship("PulseData", back_populates="device")
    location_history = relationship("LocationData", back_populates="device")

class SOSEvent(Base):
    __tablename__ = "sos_events"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.id"))
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="active") # active, resolved

    device = relationship("Device", back_populates="events")

class PulseData(Base):
    __tablename__ = "pulse_data"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.id"))
    bpm = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    device = relationship("Device", back_populates="pulse_history")

class LocationData(Base):
    __tablename__ = "location_data"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, ForeignKey("devices.id"))
    latitude = Column(Float)
    longitude = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    device = relationship("Device", back_populates="location_history")
