import os
import asyncio
import jwt
from app.config import Config
from fastapi import APIRouter, Request, Response, Form, Depends, status, Path, Cookie, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2AuthorizationCodeBearer
from .forms import LoginForm
from . import services
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
    logger.info("MQTT SUBSCRIBE")
    # asyncio.create_task(MQTTClient.subscribe(Config.MQTT_SUBSCRIBE_TOPICS_LIST))

async def get_token(request: Request):
    # print(f"HEADE: {request.headers}")
    auth = request.headers.get('auth')
    if not auth or not auth.startswith('Bearer '):
        logger.error("AUTH HEADER MISSING")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="AUTH HEADER MISSING")
    token = auth[7:]
    return token    

@router.get('/')
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
 
#=====LOGIN=====#
@router.post('/login', response_class=JSONResponse)
async def login_post(request: Request, response: Response, user_data: dict, db_session: AsyncSession = Depends(get_session)):
    try:
        username = user_data['username']
        password = user_data['password']
        auth = await services.auth_user(db_session=db_session, username=username, password=password)
        if not auth['user_id']: return auth
        logger.info(f"U_ID {auth['user_id']} LOGIN")
        token = services.create_jwt_token({"user_id":auth['user_id']})
        if token:
            return {'token': token}
        else:
            return {'error': 'Cannot create token'}
    except HTTPException as e:
        logger.error(e)
        return {'error': e.detail}
    except Exception as e:
        logger.error(e)
        return RedirectResponse("/")

@router.get('/user')
async def user_get(requset: Request, token: str = Depends(get_token), db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if not user_id:
            return {'error': 'TOKEN INVALID'}
        user = await queries.get_user_data(db_session, user_id)
        if user:
            return {'user_id': user.primary_key, 'username': user.username, 'email': user.email}
        else:
            logger.error(f"U_ID {user_id} NOT FOUND")
            return {'error': f'USER NOT FOUND'}
    except HTTPException as e:
        return {'error': e.detail}
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}

@router.post('/sign_up')
async def signup_post(request: Request, user_data: services.SignUpModel, db_session: AsyncSession = Depends(get_session)):
    res = await services.signup_user(db_session, user_data.username, user_data.email, user_data.password)
    return res

@router.post('/add_house')
async def add_house_post(request: Request, house_data: services.HouseModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    user_id = services.verify_token(token)
    house = await services.create_new_house(db_session, user_id, house_data.name)
    return house


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
    except Exception as e:
        logger.error(e)
        return {'error': 'Unexpected error'}

@router.post('/add_room')
async def add_room_post(request: Request, room_data: services.RoomModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        res = await services.add_room(db_session, user_id, room_data.house_id, room_data.name)
        if not res:
            return {'error': 'COULD NOT ADD ROOM'}
        logger.info(f'U_ID {user_id} HOUSE_ID {room_data.house_id} ADD ROOM {room_data.name}')
        return res
        
    
    
@router.delete('/delete_room')
async def delete_room(request: Request, room_data: services.RoomModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        
        res = await services.delete_room(db_session, user_id, room_data.room_id, room_data.house_id)
        if not res:
            return {'error': f'CANNOT DELETE ROOM_ID {room_data.name}'}
        return res
    
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

@router.delete('/delete_room_device')
async def del_room_device(request: Request, room_device: services.RoomDeviceModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        res = await services.delete_room_device(db_session, user_id, room_device.room_id, room_device.device_id)
        if res:
            return {'success': 'Device deleted from room and database'}
        else:
            return {'error': 'Error on the server side'}
    except Exception as e:
        logger.error(e)
        return {'error': 'Error on the server side'}