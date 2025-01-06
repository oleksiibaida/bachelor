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
    name: str
    house_id: int

class DeviceModel(BaseModel):
    dev_id: str
    name: str
    room_id: int = None
    description: str = None

class RoomDeviceModel(BaseModel):
    device_id: str
    room_id: int

def create_jwt_token(data: dict):
    payload = {**data, 'exp': time.time() + Config.JWT_EXPIRE_TIME}
    return jwt.encode(payload=payload, key=Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)

async def auth_user(username: str, password: str, session):
    if not username or not password:
        _logger.error("EMPTY DATA")
        raise ValueError("All user data mus be provided")
    user = await queries.get_user_data(db_session=session,username=username)
    if user is None:
        return None
    auth = user.verify_password(password)
    return {"user_id": user.primary_key, "auth": auth}

async def signup_user(db_session, username: str, email: str, password: str):
    if not username or not email or not password:
        _logger.error("EMPTY DATA")
        raise ValueError("All user data mus be provided")
    try:
        print("SIGNUP")
        reg = await queries.add_user(db_session, username, email, password)
        if not reg:
            return False
        user_data = await queries.get_user_data(db_session, username=username)
        if not user_data:
            return False
        token = create_jwt_token({'user_id': user_data.primary_key})
        return {'auth': True, 'token': token}
    except HTTPException as e:
        _logger.error(e)
        raise e
    
async def logout_user(db_session, user_id: int = None, username: str = None):
    if not user_id and not username:
        _logger.error("EMPTY SET")
        raise ValueError("U_ID and U_NAME are NONE")
    await queries.update_session_user(db_session=db_session, user_id=user_id, username=username,session_id="logout")

async def validate_session_user(db_session, session_id: str, user_id: int = None, username: str = None):
    if not user_id and not username:
        _logger.error("EMPTY SET")
        raise ValueError("U_ID and U_NAME are NONE")
    user = await queries.get_user_data(db_session=db_session, user_id=user_id, username=username)
    return user.session_id == session_id

async def create_new_house(db_session, user_id, houseName):
    try:
        print(f'HOUSE NAME {houseName} sdf')
        if houseName is None or len(houseName) < 1 or houseName=='': return False
        user_houses = await queries.get_houses_on_user(db_session, user_id)
        print(f'HOUSES: {user_houses}')
        # avoid doubling
        if any(house.name == houseName for house in user_houses):
            raise ValueError("House with this name already exists. Please choose another name")
        house = await queries.add_new_house(db_session, user_id, houseName)
        return house
    except HTTPException as e:
        raise e
    
async def delete_house(db_session, user_id, house_id):
    try:
        owner = await queries.verify_house_owner(db_session, user_id, house_id)
        if owner:
            res = await queries.delete_house(db_session, house_id)
            if not res: return False
            return True
        return False
    except HTTPException as e:
        _logger.error(e)
        raise e

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
            for room in house.rooms:
                room_data = {
                    "id": room.primary_key,
                    "name": room.name,
                    "devices": []
                }
                for room_device in room.devices:
                    # Extract the related DeviceModel object
                    device = room_device.device
                    if device:  # Ensure device is not None
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
        raise e

async def add_room(db_session, user_id, house_id, room_name):
    try:
        owner = await queries.verify_house_owner(db_session, user_id, house_id)
        if owner:
            res = await queries.add_new_room(db_session, house_id, room_name)
            print(res)
            return res
        return False
    except HTTPException as e:
        _logger.error(e)
        raise e
    except Exception as e:
        _logger.error(e)
        raise e
    
async def delete_room(db_session, user_id, room_id, house_id):
    try:
        owner = await queries.verify_house_owner(db_session, user_id, house_id)
        if owner:
            res = await queries.delete_room(db_session, room_id)
            if not res: return False
            res = await queries.delete_all_devices_in_room(db_session, room_id)
            if not res: return False
            return True
        return False
    except HTTPException as e:
        _logger.error(e)
        raise e

async def add_new_device(db_session, user_id, device_data):
    try:
        print("DEV DATA")
        print(device_data)
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
        return res
    except Exception as e:
        _logger.error(e)
        return e

async def delete_room_device(db_session, user_id: int, room_id: int, device_id:str):
    try:
        house_id = await queries.get_house_by_room(db_session, room_id)
        if not house_id: return False
        owner = await queries.verify_house_owner(db_session,user_id, house_id)
        if not owner: 
            _logger.error(f'U_ID {user_id} UNAUTHORIZED ACCESS TO HOUSE_ID {house_id}')
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User is not owner of this house')
        device_primary = await queries.get_device(db_session, user_id, dev_id=device_id)
        if not device_primary:
            return False
        print(f"DEVICE PRIM {device_primary.primary_key}")
        res = await queries.delete_room_device(db_session, room_id, device_primary.primary_key)
        if not res:
            return False
        # res = await queries.delete_device(db_session, device_primary_key=device_primary)
        # if not res:
        #     return False        
        return True
    except HTTPException as http_err:
        _logger.error(f"HTTP Exception: {http_err.detail}")
        raise http_err
    except Exception as e:
        _logger.critical(f"Unexpected error: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="Unexpected error")

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