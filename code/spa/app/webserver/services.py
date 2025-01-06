from ..db.models import UserModel
# from dbalchemy import db_session
from ..config import Config
from app.db import queries
import secrets
import time
import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel
_logger = Config.logger_init()

class SignUpModel(BaseModel):
    username: str
    email: str
    password: str

class HouseModel(BaseModel):
    name: str

class RoomModel(BaseModel):
    house_id: int
    room_id: int = None
    name: str = None

class DeviceModel(BaseModel):
    dev_id: str
    name: str
    room_id: int = None
    description: str = None

class RoomDeviceModel(BaseModel):
    device_id: str
    room_id: int

def create_jwt_token(data: dict):
    """
    Creates jwt token based on data
    :return: encoded jwt token
    """
    payload = {**data, 'exp': time.time() + Config.JWT_EXPIRE_TIME}
    return jwt.encode(payload=payload, key=Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)

async def auth_user(db_session, username: str, password: str):
    """
    Authenticates user
    :param username:
    :param password
    """
    try:
        if not username or not password:
            _logger.error("EMPTY DATA")
            raise ValueError("All user data mus be provided")
        user = await queries.get_user_data(db_session, username=username)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid username")
        auth = user.verify_password(password)
        return {"user_id": user.primary_key}
    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        _logger.error(e)
        return {'error': e}
    
async def signup_user(db_session, username: str, email: str, password: str):
    if not username or not email or not password:
        _logger.error("EMPTY DATA")
        return {'error': "All user data mus be provided"}
    try:
        print("SIGNUP")
        new_user_primary = await queries.add_user(db_session, username, email, password)
        if not new_user_primary:
            return False
        token = create_jwt_token({'user_id': new_user_primary})
        return {'token': token}
    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e}
    except Exception as e:
        _logger.error(e)
        return {'error': e}
    
async def create_new_house(db_session, user_id, houseName):
    try:
        if houseName is None or len(houseName) < 1 or houseName=='': return False
        house = await queries.add_new_house(db_session, user_id, houseName)
        if house:
            return {'success': f'House {houseName} added'}
        else: return {'error': 'Could not add house'}
    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        _logger.error(e)
        return {'error': e}
        
async def delete_house(db_session, user_id, house_id):
    try:
        owner = await queries.verify_house_owner(db_session, user_id, house_id)
        if owner:
            res = await queries.delete_house(db_session, house_id)
            if not res: return False
            return True
        return False
    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        _logger.error(e)
        return {'error': e}
    
async def get_houses(db_session, user_id: int):
    try:
        houses = await queries.get_houses_on_user(db_session, user_id)
        house_list = []
        for house in houses:
            house_data = {
                "id": house.primary_key,
                "name": house.name,
                "rooms": []
            }
            # from room list room is RoomModel
            for room in house.rooms:
                room_data = {
                    "id": room.primary_key,
                    "name": room.name,
                    "devices": []
                }
                # form device list room_device is RoomDeviceModel
                for room_device in room.devices: 
                    device = room_device.device
                    if device:
                        device_data = {
                            "id": device.primary_key,
                            "dev_id": device.dev_id,
                            "name": device.name,
                            "description": device.description,
                        }
                        room_data["devices"].append(device_data)
                house_data["rooms"].append(room_data)
            house_list.append(house_data)
        return house_list
    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        _logger.error(e)
        return {'error': e}

async def add_room(db_session, user_id, house_id, room_name):
    try:
        owner = await queries.verify_house_owner(db_session, user_id, house_id)
        if owner:
            res = await queries.add_new_room(db_session, house_id, room_name)
            if res:
                return {'success': f'Room {room_name} added'}
        return False
    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        _logger.error(e)
        return {'error': e}
    
async def delete_room(db_session, user_id, room_id, house_id):
    try:
        owner = await queries.verify_house_owner(db_session, user_id, house_id)
        if owner:
            res = await queries.delete_room(db_session, room_id)
            if not res: return False
            return {'success': 'Room deleted'}
        return False
    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        _logger.error(e)
        return {'error': e}
    
async def add_new_device(db_session, user_id, device_data):
    try:
        if device_data.dev_id is None or device_data.name is None:
            return False
        if device_data.room_id is not None:
            # Verify user_id is owner of the house with room_id
            house_id = await queries.get_house_by_room(db_session, device_data.room_id)
            if not house_id: return False
            owner = await queries.verify_house_owner(db_session,user_id, house_id)
            if not owner: 
                _logger.error(f'U_ID {user_id} UNAUTHORIZED ACCESS TO HOUSE_ID {house_id}')
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User is not owner of this house')
        res = await queries.add_new_device(db_session, user_id, device_data)
        if not res:
            return False
        if device_data.room_id is not None:
            res = await queries.add_room_device(db_session, res.primary_key, device_data.room_id)
            return {'success': f'Device {device_data.name} added to room {device_data.room_id}'}
        return {'success': f'Device {device_data.name} added'}
    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        _logger.error(e)
        return {'error': e}

async def delete_room_device(db_session, user_id: int, room_id: int, device_id:str):
    try:
        house_id = await queries.get_house_by_room(db_session, room_id)
        if not house_id: return False
        owner = await queries.verify_house_owner(db_session,user_id, house_id)
        if not owner: 
            _logger.critical(f'U_ID {user_id} UNAUTHORIZED ACCESS TO HOUSE_ID {house_id}')
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User is not owner of this house')
        device_primary = await queries.get_device(db_session, user_id, dev_id=device_id)
        if not device_primary:
            return False
        res = await queries.delete_room_device(db_session, room_id, device_primary.primary_key)
        if not res:
            return False      
        return {'success': 'Device deleted from room and database'}
    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        _logger.critical(f"Unexpected error: {e}")
        return {'error': e}

def verify_token(token: str):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, [Config.JWT_ALGORITHM])
        user_id = payload['user_id']
        return user_id
    except jwt.ExpiredSignatureError:
        _logger.error("Token expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        _logger.error(f'Invalid Token')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except KeyError as k:
        _logger.error(k)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing required claim")
    except Exception as e:
        _logger.exception(f"{e}") # Use logger.exception for full traceback
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")