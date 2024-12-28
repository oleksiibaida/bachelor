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
    auth = request.headers.get('authorization')
    if not auth or not auth.startswith('Bearer '):
        logger.error("AUTH HEADER MISSING")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="AUTH HEADER MISSING")
    token = auth[7:]
    return token    

@router.post('/')
@router.get('/')
async def index(request: Request):
    print("GET /")
    # await MQTTClient.publish("alarm", "get")
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
        response.set_cookie(
            key='token',
            value=token,
            httponly=True,
            # secure=True, # Need HTTPS
            samesite='strict',
            max_age=Config.JWT_EXPIRE_TIME
        )
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

#====REGISTER====#
@router.get('/register', response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request":request})

@router.post('/register')
async def register_post(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db_session: AsyncSession = Depends(get_session)):
    user_id = await queries.add_user(db_session=db_session, username=username,email=email,password=password)
    print(user_id)

#====HOME====#
# @router.post("/home")
@router.get("/home")
async def home_id_get(request: Request, db_session: AsyncSession = Depends(get_session)):
    try:
        token = request.cookies.get('token')
        print(f"TOKEN:{token}")
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        user_id = payload['user_id']
        print(f'USER ID: {user_id}')
        user = await queries.get_user_data(db_session, user_id)
        # return {"home":"ok"}
        return templates.TemplateResponse("home.html", {"request":request, "username": user.username})     
    except jwt.ExpiredSignatureError:
        logger.error("Expired JWT received for /home")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        logger.error("Invalid JWT received for /home")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except KeyError as e:
        logger.error(f"KeyError in JWT payload for /home: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing required claim")
    except Exception as e:
        logger.exception(f"Unexpected error in /home route: {e}") # Use logger.exception for full traceback
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")

@router.post('/addHouse')
async def addHouse_post(request: Request, db_session: AsyncSession = Depends(get_session)):
    house_data = await request.json()
    print(f'ADD HOUSE: {house_data['userId']}-{house_data['houseName']}')
    hs = await services.create_new_house(db_session, house_data['userId'], house_data['houseName'])
    print(hs)
    return {'data':'some data'}