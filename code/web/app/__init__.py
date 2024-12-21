from flask import Flask
from .config import Config
from .db import init_db
from .db.models import User, UserDevice
from .webserver import create_app
logger = Config.logger_init()
def create_app_instance(config):
    logger.info("START INIT")
    flask_app, db_instance = create_app(config)
    return flask_app, db_instance