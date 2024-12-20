import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

from .routes import bp

_logger = Config.logger_init()

def create_app(conf):
    app = Flask(__name__)
    db = SQLAlchemy(app)
    
    app.register_blueprint(bp)
    return app, db