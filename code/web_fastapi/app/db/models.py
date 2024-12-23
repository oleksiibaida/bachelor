from sqlalchemy import Column, Integer, String, ForeignKey, PrimaryKeyConstraint
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

class UserDeviceModel(Base):
    __tablename__ = 'userdevice'
    user = Column(Integer, ForeignKey('user.id'), nullable=False)
    device = Column(String(10), nullable=False)
    __table_args__ = (
        PrimaryKeyConstraint('user', 'device'),
    )

    # def __init__(self, user_device:dict):
    #     if user_device['user'] is None or user_device['device'] is None:
    #         __logger.error(msg=f"user_device with empty field: {[field for field in user_device if user_device[field] is None]}")
    #         return
    #     self.user = user_device['user']
    #     self.device = user_device['device']

    def __repr__(self):
        return f'<User: {self.user}; Device: {self.device}>'