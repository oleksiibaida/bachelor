from app.config import Config
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from .models import UserModel, HouseModel
from fastapi import Depends, HTTPException
from . import get_session
_logger = Config.logger_init()

async def add_user(db_session: AsyncSession, username: str, email: str, password: str):
    if username is None or email is None or password is None:
        _logger.error("All user data must be provided")
        return False
    try:
        query = insert(UserModel).values(username=username, email=email, password=password)
        await db_session.execute(query)
        await db_session.commit()
        return True
    except IntegrityError as e:
        await db_session.rollback()
        raise HTTPException(status_code=400, detail="Username or email already exists")
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

async def get_all_users(db_session: AsyncSession):
    res = await db_session.execute(select(UserModel))
    return res.scalars().all()

async def get_user_data(db_session: AsyncSession, user_id: int = None, username: str = None, email: str = None):
    if not user_id and not username and not email:
        _logger.error(msg="EMPTY SET")
        raise ValueError()
    query = select(UserModel)
    if user_id:
        query = query.where(UserModel.id == user_id)
    if username:
        query = query.where(UserModel.username == username)
    if email:
        query = query.where(UserModel.email == email)
    try:
        res = await db_session.execute(query)
        return res.scalars().one()
    except NoResultFound:
        _logger.info(msg=f"NO USER DATA FOUND FOR {user_id if user_id else username}")    
        return None
    except Exception as e:
        _logger.error(f"Error fetching user data: {e}")
        raise

async def auth_user(db_session:AsyncSession, username:str, password:str):
    if not username or not password:
        _logger.error(msg="EMPTY SET")
        raise ValueError()
    query = select(UserModel).where(UserModel.username == username)
    try:
        res = await db_session.execute(query)
        user = res.scalars().one()
        print(res)
    except NoResultFound:
        return None
    except Exception as e:
        _logger.error(f"Error auth {e}")
        raise

async def update_session_user(db_session: AsyncSession, user_id: int = None, username: str = None, session_id: str = None):
    if not user_id and not username:
        _logger.error("EMPTY SET")
        raise ValueError()
    if not session_id:
        _logger.error("session_id SET inactive")
        session_id = 'inactive'
    query = update(UserModel).values(session_id = session_id)
    if user_id:
        query.where(UserModel.id == user_id)
    if username:
        query.where(UserModel.username == username)
    try:
        res = await db_session.execute(query)
        _logger.info(f"UPDATED U_ID:{user_id} session_id:{session_id}")
        await db_session.commit()
        return res.rowcount
    except Exception as e:
        _logger.error(e)
        raise

async def get_user_by_session(db_session: AsyncSession, session_id: str):
    stmt = select(UserModel).where(UserModel.session_id == session_id)
    user = await db_session.execute(stmt)
    return user.id, user.name

async def add_new_house(db_session: AsyncSession, user_id: int, house_name: str):
    stmt = insert(HouseModel).values(name = house_name, user_id = user_id)
    try:
        await db_session.execute(stmt)
        await db_session.commit()
        stmt = select(HouseModel).where(HouseModel.user_id == user_id, HouseModel.name == house_name)
        res = await db_session.execute(stmt)
        return res.scalars().one()
    except IntegrityError as e:
        await db_session.rollback()
        raise HTTPException(status_code=400, detail="House Name already exists")
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

async def get_houses_on_user(db_session: AsyncSession, user_id: int):
    stmt = select(HouseModel).where(HouseModel.user_id == user_id)
    res = await db_session.execute(stmt)
    return res.scalars().all()

async def get_houses_and_rooms(db_session: AsyncSession, user_id: int):
    stmt = select(HouseModel).options(joinedload(HouseModel.rooms))
    res = await db_session.execute(stmt)
    return res.scalars().all()