from ..db.models import UserModel, UserDeviceModel
# from dbalchemy import db_session
from ..config import Config
from app.db import queries
_logger = Config.logger_init()

async def auth_user(username: str, password: str, session):
    if not username or not password:
        _logger.error("EMPTY DATA")
        raise ValueError("All user data mus be provided")
    user = await queries.get_user_data(session=session,username=username)
    print(user.verify_password(password))
    return user.verify_password(password)

async def register_user(username: str, email: str, password: str, session):
    if not username or not email or not password:
        _logger.error("EMPTY DATA")
        raise ValueError("All user data mus be provided")
    return 
    
    
