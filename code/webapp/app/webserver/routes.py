import os
import asyncio
from app.config import Config
from fastapi import APIRouter, Request, Response, Form, Depends, status, Path, Cookie, HTTPException, Query, WebSocket, WebSocketDisconnect, WebSocketException
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from . import services
from typing import Union
# from .services import auth_user, logout_user, validate_session_user, create_new_house
from app.db import get_session, queries
from sqlalchemy.ext.asyncio import AsyncSession
from app.mqtt.client import MQTTClient

logger = Config.logger_init()
router = APIRouter()

templates_path = os.path.join(os.path.dirname(__file__), "templates")

# oauth = OAuth2AuthorizationCodeBearer(authorizationUrl='localhost',tokenUrl="/login")
templates = Jinja2Templates(directory=templates_path)

@router.on_event("startup")
async def startup():
    logger.info(f"Startup called in process: {os.getpid()}")
    mqtt_client = MQTTClient()
    await mqtt_client.load_scenarios()
    print("S")
    asyncio.create_task(mqtt_client.start_client(Config.MQTT_SUBSCRIBE_TOPICS_LIST))

async def get_token(request: Request):
    auth = request.headers.get('auth')
    if not auth or not auth.startswith('Bearer '):
        logger.error("AUTH HEADER MISSING")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="AUTH HEADER MISSING")
    token = auth[7:]
    return token    

@router.get('/', response_class=HTMLResponse)
async def index(request: Request):
    """
    Default root link
    :return: Basic HTML-Page index.html
    """
    return templates.TemplateResponse("index.html", {'request': request})

#=====LOGIN=====#
@router.post('/login', response_model=services.TokenModel, responses={400: {"model": services.ErrorModel}})
async def login_post(request: Request, response: Response, user_data: services.UserLoginModel, db_session: AsyncSession = Depends(get_session)):
    """
    Authenticate user
    - **username**: Requiered String
    - **password**: Required String
    """
    try:
        auth = await services.auth_user(db_session=db_session, username=user_data.username, password=user_data.password)
        if not 'user_id' in auth: 
            logger.error(f"USERNAME {user_data.username} LOGIN FAILED")
            return auth
        logger.info(f"U_ID {auth['user_id']} LOGIN")
        token = services.create_jwt_token({"user_id":auth['user_id']})
        if token:
            return {'token': token}
        else:
            return {'error': 'Cannot create token'}
    except HTTPException as e:
        logger.error(f'HTTP {e}')
        return {'error': e.detail}
    except Exception as e:
        logger.error(f'UNEXPECTED {e}')
        return RedirectResponse("/")

@router.get('/get_user_data')
async def user_get(requset: Request, token: str = Depends(get_token), db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if not user_id:
            return {'error': 'TOKEN INVALID'}
        res = await services.get_user_data(db_session, user_id)
        for _ in res:
            print(_,res[_])
        return JSONResponse(res)
    except HTTPException as e:
        return {'error': e.detail}
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}

@router.post('/sign_up')
async def signup_post(request: Request, user_data: services.SignUpModel, db_session: AsyncSession = Depends(get_session)):
    """
    Sign up new user
    - **username**: Required String
    - **password**: Required String
    - **email**: Required String
    - **return**: {token: str}
    """
    res = await services.signup_user(db_session, user_data.username, user_data.email, user_data.password)
    return res

@router.post('/add_house')
async def add_house_post(request: Request, house_data: services.HouseModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    """
    Saves house in DB. Unique house name for user_id
    - **name: Required string**
    """
    try:
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        house = await services.create_new_house(db_session, user_id, house_data.name)
        return house
    except HTTPException as e:
        logger.error(e)
        return {'error': e}
    except ValueError as e:
        logger.error(e)
        return {'error': e}
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}

@router.get('/get_houses', response_class=JSONResponse)
async def get_houses(request: Request, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        house_list = await services.get_houses(db_session, user_id)
        print(house_list)
        return JSONResponse(house_list)
    except HTTPException as e:
        logger.error(e)
        return {'error': e}
    except ValueError as e:
        logger.error(e)
        return {'error': e}
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}
    
@router.delete('/delete_house')
async def delete_house(request: Request, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        body = await request.json()
        house_id = body.get('house_id')
        res = await services.delete_house(db_session, user_id, house_id)
        if res:
            return {'success': f'DELETE HOUSE_ID {house_id}'}
        else:
            return {'error': f'Problem on server side'}
    except HTTPException as e:
        logger.error(e)
        return {'error': e}
    except ValueError as e:
        logger.error(e)
        return {'error': e}
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}

@router.post('/add_room')
async def add_room_post(request: Request, room_data: services.RoomModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        res = await services.add_room(db_session, user_id, room_data.house_id, room_data.name)
        if not res:
            return {'error': 'COULD NOT ADD ROOM'}
        logger.info(f'U_ID {user_id} HOUSE_ID {room_data.house_id} ADD ROOM {room_data.name}')
        return res
    except HTTPException as e:
        logger.error(e)
        return {'error': e}
    except ValueError as e:
        logger.error(e)
        return {'error': e}
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}  
          
@router.delete('/delete_room')
async def delete_room(request: Request, room_data: services.RoomModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        
        res = await services.delete_room(db_session, user_id, room_data.room_id, room_data.house_id)
        if not res:
            return {'error': f'CANNOT DELETE ROOM_ID {room_data.name}'}
        return res
    except HTTPException as e:
        logger.error(e)
        return {'error': e}
    except ValueError as e:
        logger.error(e)
        return {'error': e}
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}  

@router.post('/add_new_device')
async def add_new_device_post(request: Request, device_data: services.DeviceModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")

        res = await services.add_new_device(db_session, user_id, device_data)
        if not res:
            return {'error': 'device not added'}
        return res        
    except HTTPException as e:
        logger.error(e)
        return {'error': e}
    except ValueError as e:
        logger.error(e)
        return {'error': e}
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}  

@router.post('/update_device')
async def update_device(request: Request, device_data: services.DeviceModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    user_id = services.verify_token(token)
    if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
    try:
        res = await queries.update_device(db_session, user_id, device_data)
        if res:
            return {'primary': res.primary_key, 'name': res.name, 'description': res.description}
    except HTTPException as e:
        logger.error(f'HTTPException:{e.status_code}.{e.detail}')
        return {'error': e.detail}
    except Exception as e:
        logger.error(e)
        return {'error': e}
     

@router.get('/get_devices')
async def get_devices(request: Request, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER UNAUTHORIZED")
        device_list = await services.get_devices(db_session, user_id)
        print(device_list)
        return JSONResponse(device_list)
    except HTTPException as e:
        logger.error(e)
        return {'error': e}
    except ValueError as e:
        logger.error(e)
        return {'error': e}
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}
    
@router.post('/handshake/{device_id}')
async def handshake(request: Request, token: str = Depends(get_token), device_id: str = Path(...), db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER UNAUTHORIZED")
        await MQTTClient.send_handshake(device_id)
    except HTTPException as e:
        logger.error(e)
        return {'error': e}        
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}
    
@router.post('/send_command/{device_id}/{command}')
async def send_command(request: Request, token: str = Depends(get_token), device_id: str = Path(...), command: str = Path(...), db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER UNAUTHORIZED")
        await services.send_command(db_session, user_id, device_id, command)
    except HTTPException as e:
        logger.error(e)
        return {'error': e}        
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}

@router.delete('/delete_device')
async def del_room_device(request: Request, room_device: services.RoomDeviceModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    try:
        print("ALALALA")
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        print("DEV DATA", room_device)
        res = await services.delete_device(db_session, user_id, device_id=room_device.device_id, room_id=room_device.room_id)
        print("RES:", res)
        if not res:
            return {'error': 'Error on the server side'}
        return res
    except Exception as e:
        logger.error(e)
        return {'error': 'aaaUnexpected Error on the server side'}

@router.websocket('/mqtt/device/{device_id}')
async def websocket_mqtt(ws: WebSocket,  device_id: str = Path(...), db_session: AsyncSession = Depends(get_session)):
    try:
        print("WEBSOCKET")
        print(device_id)
        auth = await services.WebsocketHandler.auth_websocket(db_session, ws, device_id)
        if auth:
            await services.WebsocketHandler.connect(ws, device_id)
        counter = 10
    except HTTPException as e:
        logger.error(e)
        return {'error': e}
    except ValueError as e:
        logger.error(e)
        return {'error': e}
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}
    
@router.post('/add_scenario')
async def add_scenario(request: Request, scenario_data: services.ScenarioModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        print("SCENARIO DATA:", scenario_data)
        res = await services.add_scenario(db_session, user_id, scenario_data)
        print(res)
        return res
    except HTTPException as e:
        logger.error(e)
        return {'error': e}
    except ValueError as e:
        logger.error(e)
        return {'error': e}
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}
    
@router.delete('/delete_scenario')
async def delete_scenario(request: Request, token: str = Depends(get_token), db_session: AsyncSession = Depends(get_session)):
    try:
        print(request)
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        body = await request.json()
        scenario_primary = body.get("scenario_primary")
        res = await services.delete_scenario(db_session, user_id, scenario_primary)
        if res:
            return {"success": f"Scenario {scenario_primary} DELETED"}
        return res
    except HTTPException as e:
        logger.error(e)
        return {'error': e}
    except ValueError as e:
        logger.error(e)
        return {'error': e}
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}    