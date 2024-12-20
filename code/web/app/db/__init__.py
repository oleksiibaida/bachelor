from flask_sqlalchemy import SQLAlchemy
from app.config import Config
from . import models
from .base import Base

logger = Config.logger_init()

db = SQLAlchemy()

__all__=["Base", "models"]

def init_db(app):
    logger.info(msg=f"START")
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
    app.secret_key = Config.SQLALCHEMY_SECRET_KEY
    db.init_app(app)

    with app.app_context():
        from . import models
        db.create_all()
"""
@app.teardown_appcontext
def teardown_app(error):
    db_session.remove()
    if error is not None:
        _logger.error(msg=error)
"""