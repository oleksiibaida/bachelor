import os
import asyncio
from app.config import Config
from fastapi import APIRouter, Request, Response, Form, Depends, status, Path, Cookie, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from .forms import LoginForm
from .services import auth_user, logout_user, validate_session_user
from app.db import get_session, queries
from sqlalchemy.ext.asyncio import AsyncSession
from app.mqtt.client import MQTTClient
logger = Config.logger_init()
router = APIRouter()
templates_path = os.path.join(os.path.dirname(__file__), "templates")

templates = Jinja2Templates(directory=templates_path)

@router.on_event("startup")
async def startup():
    logger.info("MQTT SUBSCRIBE")
    # asyncio.create_task(MQTTClient.subscribe(Config.MQTT_SUBSCRIBE_TOPICS_LIST))
    

@router.get('/')
async def index(request: Request):
    print("GET /")
    # await MQTTClient.publish("alarm", "get")
    return templates.TemplateResponse("index.html", {"request": request})
#=====LOGIN=====#
@router.post('/login')
async def login_post(request: Request, username: str=Form(...), password: str=Form(...), db_session: AsyncSession = Depends(get_session)):
    # auth_user(username, password)
    try:
        print("AUTH")
        auth = await auth_user(username=username, password=password, session=db_session)
        if auth is None:
            raise HTTPException("Invalid username or password")
        logger.info("LOGIN SUCCESSFULL")
        for a in auth:
            print(auth[a])
        response = RedirectResponse(f"/home/{auth['user_id']}")
        response.set_cookie("session_id", auth['session_id'])
        return response
    except Exception as e:
        logger.error(e)
        return RedirectResponse("/")

@router.get("/logout/{user_id}")
async def logout_get(request: Request, user_id: int = Path(...), session_id: str = Cookie(None), db_session: AsyncSession = Depends(get_session)):
    await logout_user(db_session=db_session, user_id=user_id)
    response = RedirectResponse('/')
    response.set_cookie("session_id", "logout")
    return 

#====REGISTER====#
@router.get('/register', response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request":request})

@router.post('/register')
async def register_post(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db_session: AsyncSession = Depends(get_session)):
    user_id = await queries.add_user(db_session=db_session, username=username,email=email,password=password)
    print(user_id)

#====HOME====#
@router.post("/home/{user_id}")
# @router.get("/home/{user_id}")
async def home_id_get(request: Request, user_id: int = Path(...), session_id: str = Cookie(None), db_session: AsyncSession = Depends(get_session)):
    if session_id is None:
        return RedirectResponse("/", status_code=303)
    # validate_session = validate_session_user(db_session, session_id, user_id)
    user = await queries.get_user_data(db_session=db_session, user_id=user_id)
    if user.session_id == session_id:
        return templates.TemplateResponse("home.html", {"request":request, "username": user.username, "user_id": user.id})
    return RedirectResponse("/")