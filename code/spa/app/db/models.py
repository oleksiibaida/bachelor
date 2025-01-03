from sqlalchemy import Column, Integer, String, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.schema import UniqueConstraint
from .base import Base
from app.config.logger_config import logger_init
__logger = logger_init()
class UserModel(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(200), nullable=False)
    session_id = Column(String(50), nullable=True)
    def __repr__(self):
        return f'<U_ID:{self.id} U_NM:{self.username}>' #{self.id, self.username, self.email, self.pasword}    
    
    def verify_password(self, password:str):
        return self.password == password

class HouseModel(Base):
    __tablename__ = 'house'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    rooms = relationship("RoomModel", backref="house", cascade="all, delete-orphan", lazy='selectin')

    __table_args__ = (UniqueConstraint('name', 'user_id'),)

class RoomModel(Base):
    __tablename__ = 'room'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    name = Column(String(50), nullable=False)
    house_id = Column(Integer, ForeignKey('house.id'), nullable=False)
    devices = relationship('DeviceModel', backref='room', cascade="all, delete-orphan", lazy='selectin')

class DeviceUserRoomModel(Base):
    __tablename__ = 'device'
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    dev_id = Column(String(10), nullable=False)
    name = Column(String(50), nullable=False)
    user_id = Column(Integer, nullable=False, unique=False)
    room_id = Column(Integer, ForeignKey("room.id"), nullable=True)
    desciption = Column(String(250), nullable=True)