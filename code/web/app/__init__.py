from flask import Flask
from .config import Config
from .db import db
from .db.models import User, UserDevice
from .webserver import create_app

def create_app_instance(config):
    flask_app, db_instance = create_app(config)
    return flask_app, db_instance