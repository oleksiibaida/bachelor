from flask import Flask
from .database import Database
from config.logger_config import logger_init

_logger = logger_init()

def create_app():
    
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'mysecret'
    db = Database()
    from app.routes import register_routes
    register_routes(app, db=db)

    # @app.before_request
    # def initialize_database():
    #     db.create_tables()
        
    
    return app