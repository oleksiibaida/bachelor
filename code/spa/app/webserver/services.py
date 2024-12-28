from ..db.models import UserModel
# from dbalchemy import db_session
from ..config import Config
from app.db import queries
import secrets
import time
import jwt
from fastapi import HTTPException, status
from pydantic import BaseModel
_logger = Config.logger_init()

class SignUpModel(BaseModel):
    username: str
    email: str
    password: str

class HouseModel(BaseModel):
    name: str

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

async def signup_user(db_session, username: str, email: str, password: str):
    if not username or not email or not password:
        _logger.error("EMPTY DATA")
        raise ValueError("All user data mus be provided")
    try:
        reg = await queries.add_user(db_session, username, email, password)
        if not reg:
            return False
        user_data = await queries.get_user_data(db_session, username=username)
        if not user_data:
            return False
        token = create_jwt_token({'user_id': user_data.id})
        return {'auth': True, 'token': token}
    except HTTPException as e:
        _logger.error(e)
        raise e
    
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
    try:
        user_houses = await queries.get_houses_on_user(db_session, user_id)
        print(f'HOUSES: {user_houses}')
        # avoid doubling
        if any(house.name == houseName for house in user_houses):
            raise ValueError("House with this name already exists. Please choose another name")
        house = await queries.add_new_house(db_session, user_id, houseName)
        return house
    except HTTPException as e:
        raise e

async def get_houses(db_session, user_id: int):
    try:
        houses = await queries.get_houses_on_user(db_session, user_id)
        house_list = []
        for h in houses:
            house_data = {'name': h.name}
            house_list.append(house_data)
        return house_list
    except HTTPException as e:
        raise e

def verify_token(token: str):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, [Config.JWT_ALGORITHM])
        user_id = payload['user_id']
        return user_id
    except jwt.ExpiredSignatureError:
        _logger.error("Token expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except jwt.InvalidTokenError:
        _logger.error(f'Invalid Token')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except KeyError as k:
        _logger.error(k)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing required claim")
    except Exception as e:
        _logger.exception(f"{e}") # Use logger.exception for full traceback
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server error")