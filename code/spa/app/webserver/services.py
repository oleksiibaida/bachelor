from ..db.models import UserModel
# from dbalchemy import db_session
from ..config import Config
from app.db import queries
import secrets
import time
import jwt
import json
from app.mqtt.client import MQTTClient
from fastapi import HTTPException, status, WebSocket, WebSocketException
from fastapi.websockets import WebSocketDisconnect
from pydantic import BaseModel
_logger = Config.logger_init()

class UserLoginModel(BaseModel):
    username: str
    password: str

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
    primary: int = None
    room_id: int = None
    description: str = None
    dev_type: str = None

class RoomDeviceModel(BaseModel):
    device_id: str
    room_id: int = None

class ScenarioModel(BaseModel):
    source_dev: str
    data_field: str    
    condition: str
    value: int
    target_dev: str
    command: str

class WebsocketHandler:
    active_connections = []  # Store active WebSocket connections with device_id

    @classmethod
    async def auth_websocket(cls, db_session, ws: WebSocket, device_id):
        try:
            await ws.accept()
            auth_message = await ws.receive_json()
            token = auth_message.get("auth")
            if not token or not token.startswith("Bearer "):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="AUTH HEADER MISSING")
            # Token starts at index 7
            user_id = verify_token(token[7:])
            if not user_id:
                _logger.error("USER NOT FOUND")
                ws.close()
                return False
            # user_devices = await get_devices(db_session, user_id)
            # if not any(device["dev_id"] == device_id for device in user_devices):
            #     ws.close()
            #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"U_ID {user_id} is not owner of DEV_ID {device_id}")
            owner = await queries.verify_user_device(db_session, user_id, device_id)
            return True if owner else False
        except HTTPException as e:
            _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
            raise e
        except Exception as e:
            _logger.error(e)

    @classmethod
    async def connect(cls, ws: WebSocket, device_id: str):
        new_connection = {
            'device_id': device_id,
            'websocket': ws
        }
        cls.active_connections.append(new_connection)
        
        _logger.info(f"CONNECTED WEBSOCKET DEVICE {device_id}")

        try:
            while True:
                ws_data = await ws.receive_text()
                await cls.received_data(ws, ws_data)
        except WebSocketDisconnect:
            _logger.warning("Connection closed by the client")
        except WebSocketException as e:
            _logger.warning(f"WebSocketException: Reason: {e.reason}")
        except Exception as e:
            _logger.warning(e)
        finally:
            await cls.disconnect(ws)
    
    @classmethod
    async def disconnect(cls, ws: WebSocket):
        """Remove WebSocket connection."""
        cls.active_connections = [
            con for con in cls.active_connections if con['websocket'] != ws
        ]
        _logger.info("DISCONNECTED WEBSOCKET")

    @classmethod
    async def send_data(cls, device_id: str, data):
        for con in cls.active_connections:
            if con['device_id'] == device_id:
                try:
                    await con['websocket'].send_json(data)
                    _logger.debug(f"SENT TO WEBSOCKET DEV_ID {device_id}: {data}")
                except Exception as e:
                    _logger.error(f"ERROR SEND TO WEBSOCKET DEV_ID {device_id}: {e}")
                    await cls.disconnect(con['websocket'])
                # break
    
    @classmethod
    async def received_data(cls, ws:WebSocket, data):
            for con in cls.active_connections:
                if con['websocket'].headers.get("sec-websocket-key") == ws.headers.get("sec-websocket-key"):
                    
                    topic = f'command/{con['device_id']}'
                    
                    from app.mqtt.client import MQTTClient
                    await MQTTClient.publish(topic, data) 
                    
                    break


    @classmethod
    def test(cls):
        
        print(cls.active_connections)


def create_jwt_token(data: dict):
    """
    Creates jwt token based on data
    :param data: {"user_id": user_id} 
    :return: encoded jwt token
    """
    payload = {**data, 'exp': time.time() + Config.JWT_EXPIRE_TIME}
    return jwt.encode(payload=payload, key=Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)

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
        _logger.exception(f"{e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")

async def auth_user(db_session, username: str, password: str):
    """
    Authenticates user
    :param username:
    :param password:
    """
    try:
        if not username or not password:
            _logger.error("EMPTY DATA")
            raise ValueError("All user data mus be provided")
        user = await queries.get_user_data(db_session, username=username)
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid username")
        auth = user.verify_password(password)
        if auth:
            return {"user_id": user.primary_key}
        else:
            return {'error': 'Wrong password'}
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
    
async def get_user_data(db_session, user_id):
    try:
        user = await queries.get_user_data(db_session, user_id)
        user_data = {
            'user_id': user.primary_key,
            'username': user.username,
            'email': user.email
        }
        houses = await get_houses(db_session, user_id)
        scenarios = []
        all_scenarios = await queries.get_scenarios_on_user(db_session, user_id)
        for s in all_scenarios:
            scene = {
                'id': s.primary_key,
                'source_dev': s.source_dev,
                'data_field': s.data_field,
                'condition': s.condition.value,
                'value': s.value,
                'target_dev': s.target_dev,
                'command': s.command
            }
            scenarios.append(scene)

        data = {
            "user_data": user_data,
            "houses":houses,
            "scenarios":scenarios,
            "conditions":queries.get_scenario_conditions()
        }
        return data
        
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
        house = await queries.get_house(db_session, house_id)
        # owner = await queries.verify_house_owner(db_session, user_id, house_id)
        if house.user_id != user_id:
            _logger.error(f'U_ID {user_id} UNAUTHORIZED ACCESS TO HOUSE_ID {house.primary_key}')
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User is not owner of this house')
        res = await queries.delete_house(db_session, house_id)
        if not res: return False
        return True
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
                            "dev_type": device.dev_type
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
        house = await queries.get_house(db_session, house_id)
        # verify user owns the house
        if house.user_id != user_id:
            _logger.error(f'U_ID {user_id} UNAUTHORIZED ACCESS TO HOUSE_ID {house.primary_key}')
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User is not owner of this house')
        res = await queries.add_new_room(db_session, house_id, room_name)
        return res if res else False
    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        _logger.error(e)
        return {'error': e}
    
async def delete_room(db_session, user_id, room_id, house_id):
    try:
        house = await queries.get_house(db_session, house_id)
        if house.user_id != user_id:
            _logger.error(f'U_ID {user_id} UNAUTHORIZED ACCESS TO HOUSE_ID {house.primary_key}')
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User is not owner of this house')
        res = await queries.delete_room(db_session, room_id)
        if res: 
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
        if device_data.dev_id is None:
            return False
        # If name not given => name = ID
        if device_data.name is None:
            device_data.name = device_data.dev_id
        if device_data.room_id is not None:
            # Verify user_id is owner of the house with room_id
            house = await queries.get_house_by_room(db_session, device_data.room_id)
            if not house: return False
            # owner = await queries.verify_house_owner(db_session,user_id, house_id)
            if house.user_id != user_id: 
                _logger.error(f'U_ID {user_id} UNAUTHORIZED ACCESS TO HOUSE_ID {house.primary_key}')
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User is not owner of this house')
        new_device = await queries.add_new_device(db_session, user_id, device_data)
        if not new_device:
            return False
        if device_data.room_id is not None:
            new_room_device = await queries.add_room_device(db_session, new_device.primary_key, device_data.room_id)
            _logger.debug(f'Device {device_data.name} added to room {device_data.room_id}')
            return [new_device, new_room_device]
        return new_device
    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        _logger.error(e)
        return {'error': e}
    
async def get_devices(db_session, user_id: int):
    try:
        devices = await queries.get_devices_on_user(db_session, user_id)
        device_list = []
        for dev in devices:
            if dev:
                device_data = {
                    'primary': dev.primary_key,
                    'dev_id': dev.dev_id,
                    'name': dev.name,
                    'description': dev.description,
                    'room': []
                }
                # room_device is RoomDeviceModel
                for room_device in dev.dev_rooms:
                    if room_device:
                        room = room_device.room # RoomModel
                        room_data = {
                            'id': room.primary_key,
                            'name': room.name,
                            'house_id': room.house_id
                        }
                        device_data['room'].append(room_data)
                device_list.append(device_data)
        return device_list

    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        _logger.error(e)
        return {'error': e}
   

async def delete_device(db_session, user_id: int, device_id: str, room_id: int = None ):
    try:
        # if room_id:
        #     house_id = await queries.get_house_by_room(db_session, room_id)
        #     if not house_id: return False
        #     owner = await queries.verify_house_owner(db_session,user_id, house_id)
        #     if not owner: 
        #         _logger.critical(f'U_ID {user_id} UNAUTHORIZED ACCESS TO HOUSE_ID {house_id}')
        #         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User is not owner of this house')
        device = await queries.get_device(db_session, user_id, dev_id=device_id)
        if not device:
            return False
        res = await queries.delete_device(db_session, device_primary_key=device.primary_key)
        # print(res)
        if not res:
            return False 
        return {'success': 'Device deleted from room and database'}
    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        _logger.critical(f"Unexpected error: {e}")
        return {'error': e}
    
async def add_new_scenario(db_session, user_id, scenario_data: ScenarioModel):
    try:
        # Check if user has provided devices
        device_owner = await queries.verify_user_device(db_session, user_id, scenario_data.source_dev)
        if device_owner:
            device_owner = await queries.verify_user_device(db_session, user_id, scenario_data.target_dev)
        if not device_owner:
            _logger.error(f'U_ID {user_id} UNAUTHORIZED ACCESS TO DEVICE')
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User is not owner of this device')
        res = await queries.add_scenario(
            db_session, 
            user_id=user_id, 
            source_dev=scenario_data.source_dev,
            data_field=scenario_data.data_field,
            condition=scenario_data.condition,
            value=scenario_data.value,
            target_dev=scenario_data.target_dev,
            command=scenario_data.command
        )
        
        return res
    except HTTPException as e:
        _logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        _logger.error(e)
        return {'error': e}