from app.models import User, UserDevice
# from dbalchemy import db_session
from config.logger_config import logger_init
from wtforms import ValidationError
_logger = logger_init()

class validate_user():
    def validate_username(self, db_session, username):
        if db_session.query(User).filter(User.username == username).count > 0:
            raise ValidationError('Email already exists. Please choose a different one.')

    def validate_email(self, db_session, email):
        if db_session.query(User).filter(User.email == email).count > 0:
            raise ValidationError('Email already exists. Please choose a different one.')

    def validate_user_login(self, db_session, username, password):
        _logger.info(msg="LOGIN")
        user = db_session.query(User).filter(User.username == username).first()
        _logger.info(msg=f"USER:{user}")
        if user:
            return user.pasword == password