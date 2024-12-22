import os
import asyncio
from app.config import Config
from fastapi import APIRouter, Request, Response, Form, Depends, status
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from .forms import LoginForm
from .services import auth_user
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
    await MQTTClient.publish("alarm", "get")
    return templates.TemplateResponse("index.html", {"request": request})
#=====LOGIN=====#
@router.post('/login')
async def login_post(request: Request, username: str=Form(...), password: str=Form(...), session: AsyncSession = Depends(get_session)):
    # auth_user(username, password)
    auth = await auth_user(username=username, password=password, session=session)
    if auth:
        print("USER LOGGED IN")

#====REGISTER====#
@router.get('/register', response_class=HTMLResponse)
async def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request":request})

@router.post('/register')
async def register_post(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), session: AsyncSession = Depends(get_session)):
    user_id = await queries.add_user(session=session, username=username,email=email,password=password)
    print(user_id)
