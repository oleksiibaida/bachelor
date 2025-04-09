import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from app.config import Config

from .routes import router
_logger = Config.logger_init()
_logger.info("INIT WEBSERVER")

app = FastAPI()
# def init_fastapi():
static_path = os.path.join(os.path.dirname(__file__), "static")
app.add_middleware(SessionMiddleware, secret_key=Config.SQLALCHEMY_SECRET_KEY)
app.mount("/static", StaticFiles(directory=static_path), name="static")
app.include_router(router)