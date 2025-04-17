import bcrypt
import enum
from sqlalchemy import Column, Integer, String, ForeignKey, PrimaryKeyConstraint, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from .base import Base


class UserModel(Base):
    __tablename__ = 'user'
    primary_key = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)

    def verify_password(self, password:str):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)

class HouseModel(Base):
    __tablename__ = 'house'
    primary_key = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("user.primary_key", ondelete='CASCADE'), nullable=False)
    rooms = relationship("RoomModel", backref="house", cascade="all, delete-orphan", lazy='selectin')

    __table_args__ = (UniqueConstraint('name', 'user_id'),)

class RoomModel(Base):
    __tablename__ = 'room'
    primary_key = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(50), nullable=False)
    house_id = Column(Integer, ForeignKey('house.primary_key', ondelete='CASCADE'), nullable=False)
    
    devices = relationship("RoomDeviceModel", back_populates="room", cascade="all, delete-orphan", lazy='selectin')

    __table_args__ = (UniqueConstraint('name', 'house_id'),)

class ScenarioModel(Base):
    class ScenarioConditionsEnum(enum.Enum):
        greater = ">"
        less = "<"
        equal = "=="

    __tablename__ = "scenario"

    primary_key = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(20), nullable=False)
    user_id = Column(Integer, ForeignKey("user.primary_key", ondelete='CASCADE'), nullable=False)
    source_dev = Column(String(20), ForeignKey("device.dev_id", ondelete='CASCADE'), nullable=False)
    data_field = Column(String(20), nullable=False)
    condition = Column(Enum(ScenarioConditionsEnum), nullable=False)
    value = Column(Integer, nullable=False)
    target_dev = Column(String(20), ForeignKey("device.dev_id", ondelete='CASCADE'), nullable=False)
    command = Column(String(50), nullable=False)

    if_device = relationship("DeviceModel", foreign_keys=[source_dev], lazy='selectin')
    then_device = relationship("DeviceModel", foreign_keys=[target_dev], lazy='selectin')

class DeviceModel(Base):

    __tablename__ = 'device'
    primary_key = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    dev_id = Column(String(20), nullable=False)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('user.primary_key', ondelete='CASCADE'), nullable=False, unique=False)
    description = Column(String(250), nullable=True)
    data_fields = Column(String(256), nullable=True)
    commands = Column(String(256), nullable=True)

    dev_rooms = relationship("RoomDeviceModel", back_populates="device", cascade="all, delete-orphan", lazy='selectin')
    
    scenarios_if = relationship("ScenarioModel", foreign_keys=[ScenarioModel.source_dev], back_populates="if_device", cascade="all, delete-orphan", lazy="selectin")
    scenarios_then = relationship("ScenarioModel", foreign_keys=[ScenarioModel.target_dev], back_populates="then_device", cascade="all, delete-orphan", lazy="selectin")
    __table_args__ = (UniqueConstraint('user_id', 'dev_id'),)

class RoomDeviceModel(Base):
    __tablename__ = 'room_device'
    primary_key = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    room_id = Column(Integer, ForeignKey('room.primary_key', ondelete='CASCADE'), nullable=False)
    device_primary = Column(Integer, ForeignKey('device.primary_key', ondelete='CASCADE'), nullable=False)

    room = relationship("RoomModel", back_populates="devices")
    device = relationship("DeviceModel", back_populates="dev_rooms")

    __table_args__ = (UniqueConstraint('room_id', 'device_primary'),)