import os
import asyncio
import jwt
from app.config import Config
from fastapi import APIRouter, Request, Response, Form, Depends, status, Path, Cookie, HTTPException
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

@router.post('/')
@router.get('/')
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
 
#=====LOGIN=====#
@router.post('/login')
async def login_post(request: Request, response: Response, user_data: dict, db_session: AsyncSession = Depends(get_session)):
    try:
        username = user_data['username']
        password = user_data['password']
        auth = await services.auth_user(username=username, password=password, session=db_session)
        if auth is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        logger.info(f"LOGIN {username}")
        token = services.create_jwt_token({"user_id":auth['user_id']})

        return {'auth': auth['auth'], 'token': token}
    except Exception as e:
        logger.error(e)
        return RedirectResponse("/")

@router.get("/logout/{user_id}")
async def logout_get(request: Request, user_id: int = Path(...), session_id: str = Cookie(None), db_session: AsyncSession = Depends(get_session)):
    await services.logout_user(db_session=db_session, user_id=user_id)
    response = RedirectResponse('/')
    response.set_cookie("session_id", "logout")
    return response

@router.get('/user')
async def user_get(requset: Request, token: str = Depends(get_token), db_session: AsyncSession = Depends(get_session)):
    user_id = services.verify_token(token)
    if not user_id:
        return {'error': 'TOKEN INVALID'}
    user = await queries.get_user_data(db_session, user_id)
    if user:
        return {'user_id': user.id, 'username': user.username, 'email': user.email}
    else:
        logger.error(f"U_ID {user_id} NOT FOUND")
        return {'error': f'U_ID {user_id} NOT FOUND'}

@router.post('/sign_up')
async def register_post(request: Request, user_data: services.SignUpModel, db_session: AsyncSession = Depends(get_session)):
    if not user_data.username or not user_data.email or not user_data.password:
        raise HTTPException("EMPTY SET")    
    res = await services.signup_user(db_session, user_data.username, user_data.email, user_data.password)
    if not res:
        logger.error('SIGNUP ERROR')
        return {'error': 'SIGNUP ERROR'}
    return res

@router.post('/add_house')
async def addHouse_post(request: Request, house_data: services.HouseModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    print("ADD HOUSE")
    try:
        user_id = services.verify_token(token)
        house = await services.create_new_house(db_session, user_id, house_data.name)
        if house:
            print(f"ADD HOUSE ID {house}")
            return {'data':'some data'}
        else:
            raise ValueError('House Name is empty')
    except HTTPException as e:
        logger.error(e)
        return {'error':e}
    except ValueError as e:
        logger.error(e)
        return {'error': 'NAME EXISTS'}

@router.get('/get_houses')
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
    
@router.delete('/delete_house/{house_id}')
async def delete_house(request: Request, house_id: int = Path(...), token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        res = await services.delete_house(db_session, user_id, house_id)
        print("DELETE HOUSE")
        if res:
            return {'success': f'DELETE HOUSE_ID {house_id}'}
        else:
            return {'error': f'Problem on server side'}
    except Exception as e:
        logger.error(e)
    return

@router.post('/add_room')
async def add_room_post(request: Request, room_data: services.RoomModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    try:
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        res = await services.add_room(db_session, user_id, room_data.house_id, room_data.name)
        if res:
            logger.info(f'U_ID {user_id} HOUSE_ID {room_data.house_id} ADD ROOM {room_data.name}')
            return {'success': f'U_ID {user_id} HOUSE_ID {room_data.house_id} ADD ROOM {room_data.name}'}
        return {'error': 'COULD NOT ADD ROOM'}
    except HTTPException as e:
        logger.error(e)
        return {'error': e}
    
@router.delete('/delete_room/{house_id}/{room_id}')
async def delete_room(request: Request, house_id: int = Path(...), room_id: int = Path(...), token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    try:
        print("DELETE ROOM")
        print(house_id, room_id)
        user_id = services.verify_token(token)
        if user_id is None or user_id < 0: raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="USER NOT FOUND")
        
        res = await services.delete_room(db_session, user_id, room_id, house_id)
        if res:
            return {'success':f'DELETED ROOM_ID {room_id}'}
        return {'error': f'CANNOT DELETE ROOM_ID {room_id}'}
    except HTTPException as e:
        logger.error(e)
        return {'error': f'ROOM_ID {room_id} COULD NOT BE DELETED'}
    
@router.post('/add_device')
async def add_device_post(request: Request, room_data: services.RoomModel, token: str = Depends(get_token),db_session: AsyncSession = Depends(get_session)):
    try:
        return
    except HTTPException as e:
        logger.error(e)