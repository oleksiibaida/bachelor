from sqlalchemy import Column, Integer, String, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from .base import Base
from app.config import Config
__logger = Config.logger_init()


class UserModel(Base):
    __tablename__ = 'user'
    primary_key = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    # def __repr__(self):
    #     return f'<U_ID:{self.primary_key} U_NM:{self.username}>' #{self.primary_key, self.username, self.email, self.pasword}    
    
    def verify_password(self, password:str):
        return self.password == password

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

class DeviceModel(Base):
    __tablename__ = 'device'
    primary_key = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    dev_id = Column(String(10), nullable=False)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey('user.primary_key', ondelete='CASCADE'), nullable=False, unique=False)
    description = Column(String(250), nullable=True)
    dev_rooms = relationship("RoomDeviceModel", back_populates="device", cascade="all, delete-orphan", lazy='selectin')

    __table_args__ = (UniqueConstraint('user_id', 'dev_id', 'name'),)

class RoomDeviceModel(Base):
    __tablename__ = 'room_device'
    primary_key = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    room_id = Column(Integer, ForeignKey('room.primary_key', ondelete='CASCADE'), nullable=False)
    device_primary = Column(Integer, ForeignKey('device.primary_key', ondelete='CASCADE'), nullable=False)

    room = relationship("RoomModel", back_populates="devices")
    device = relationship("DeviceModel", back_populates="dev_rooms")

    __table_args__ = (UniqueConstraint('room_id', 'device_primary'),)