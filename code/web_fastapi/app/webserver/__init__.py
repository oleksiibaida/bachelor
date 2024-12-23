import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.config import Config

from .routes import router
app = FastAPI()


# def init_fastapi():
_logger = Config.logger_init()
_logger.info("INIT WEBSERVER")
static_path = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_path), name="static")
app.include_router(router)

# app.mount("/templates", StaticFiles(directory="app/webserver/templates"), name="templates")