import os
from fastapi import APIRouter, Request, Response, Form, Depends, status
from fastapi.responses import JSONResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from .forms import LoginForm
from .services import auth_user
from app.db import get_session, queries
from sqlalchemy.ext.asyncio import AsyncSession
router = APIRouter()
templates_path = os.path.join(os.path.dirname(__file__), "templates")

templates = Jinja2Templates(directory=templates_path)

@router.get('/')
def index(request: Request):
    print("GET /")
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