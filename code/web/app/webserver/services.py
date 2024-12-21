from ..db.models import User, UserDevice
# from dbalchemy import db_session
from ..config import Config
from wtforms import ValidationError
_logger = Config.logger_init()


def validate_username(db_session, username):
    if db_session.query(User).filter(User.username == username).count() > 0:
        raise ValidationError('Email already exists. Please choose a different one.')

def validate_email(db_session, email):
    if db_session.query(User).filter(User.email == email).count() > 0:
        raise ValidationError('Email already exists. Please choose a different one.')

def validate_user_login(db_session, username, password):
    _logger.info(msg="LOGIN")
    user = db_session.query(User).filter(User.username == username).first()
    _logger.info(msg=f"USER:{user}")
    if user:
        return user.pasword == password
    else: return False