import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

from .routes import bp

_logger = Config.logger_init()

def create_app(conf):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = conf.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = conf.SQLALCHEMY_TRACK_MODIFICATIONS
    app.secret_key = conf.SQLALCHEMY_SECRET_KEY
    db = SQLAlchemy(app)
    # db.init_app(app)
    app.register_blueprint(bp)
    return app, db