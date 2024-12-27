from ..db.models import UserModel
# from dbalchemy import db_session
from ..config import Config
from app.db import queries
import secrets
import time
import jwt
_logger = Config.logger_init()

def create_jwt_token(data: dict):
    payload = {**data, 'exp': time.time() + Config.JWT_EXPIRE_TIME}
    return jwt.encode(payload=payload, key=Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)

async def auth_user(username: str, password: str, session):
    if not username or not password:
        _logger.error("EMPTY DATA")
        raise ValueError("All user data mus be provided")
    user = await queries.get_user_data(db_session=session,username=username)
    if user is None:
        return None
    session_id = secrets.token_hex(32)
    auth = user.verify_password(password)
    # if auth:
    #     await queries.update_session_user(db_session=session, session_id=session_id, username=username)
    return {"user_id": user.id, "auth": auth, "session_id": session_id}

async def register_user(username: str, email: str, password: str, session):
    if not username or not email or not password:
        _logger.error("EMPTY DATA")
        raise ValueError("All user data mus be provided")
    return 
    
async def logout_user(db_session, user_id: int = None, username: str = None):
    if not user_id and not username:
        _logger.error("EMPTY SET")
        raise ValueError("U_ID and U_NAME are NONE")
    await queries.update_session_user(db_session=db_session, user_id=user_id, username=username,session_id="logout")

async def validate_session_user(db_session, session_id: str, user_id: int = None, username: str = None):
    if not user_id and not username:
        _logger.error("EMPTY SET")
        raise ValueError("U_ID and U_NAME are NONE")
    user = await queries.get_user_data(db_session=db_session, user_id=user_id, username=username)
    return user.session_id == session_id

async def create_new_house(db_session, user_id, houseName):
    houses = await queries.get_houses_on_user(db_session, user_id)
    print(f'HOUSES: {houses}')
    if len(houses) > 0:
        for house in houses:
            if house.name == houseName:
                return ValueError("houseName already exists")
    res = await queries.add_new_house(db_session, user_id, houseName)
    return res
