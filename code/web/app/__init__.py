import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config.logger_config import logger_init
from config.app_config import FlaskConfig
from .dbalchemy import db_session, Base, engine

_logger = logger_init()

app=Flask(__name__)
app.config.from_object(FlaskConfig)
# db = SQLAlchemy(app) 
# migrate = Migrate(app=app, db=db)

from . import routes
from . import models
Base.metadata.create_all(bind=engine)

@app.teardown_appcontext
def teardown_app(error):
    db_session.remove()
    if error is not None:
        _logger.error(msg=error)