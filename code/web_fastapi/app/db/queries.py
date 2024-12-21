from app.config import Config
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from .models import UserModel, UserDeviceModel
from fastapi import Depends, HTTPException
from . import get_session
_logger = Config.logger_init()

async def add_user(session: AsyncSession, username: str, email: str, password: str):
    if username is None or email is None or password is None:
        _logger.error("All user data must be provided")
        return False
    try:
        query = insert(UserModel).values(username=username, email=email, password=password)
        await session.execute(query)
        await session.commit()
        return True
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

async def get_all_users(session: AsyncSession):
    res = await session.execute(select(UserModel))
    return res.scalars().all()

async def get_user_data(session: AsyncSession, user_id: int = None, username: str = None, email: str = None):
    if not user_id and not username and not email:
        _logger.error(msg="EMPTY SET")
        raise ValueError()
    query = select(UserModel)
    if user_id:
        query.where(UserModel.id == user_id)
    if username:
        query.where(UserModel.username == username)
    if email:
        query.where(UserModel.email == email)
    try:
        res = await session.execute(query)
        return res.scalars().one()
    except NoResultFound:
        _logger.info(msg=f"NO USER DATA FOUND FOR {user_id if user_id else username}")    
        return None
    except Exception as e:
        _logger.error(f"Error fetching user data {e}")
        raise

async def auth_user(session:AsyncSession, username:str, password:str):
    if not username or not password:
        _logger.error(msg="EMPTY SET")
        raise ValueError()
    query = select(UserModel).where(UserModel.username == username)
    try:
        res = await session.execute(query)
        user = res.scalars().one()
        print(res)
    except NoResultFound:
        return None
    except Exception as e:
        _logger.error(f"Error auth {e}")
        raise
    