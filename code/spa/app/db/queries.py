from app.config import Config
from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from .models import UserModel, HouseModel, RoomModel, DeviceModel, RoomDeviceModel
from fastapi import Depends, HTTPException
from . import get_session
_logger = Config.logger_init()

async def add_user(db_session: AsyncSession, username: str, email: str, password: str):
    """
    Adds new user to Database. SIGNUP.
    :param db_session: SQLAlchemy AsyncSession
    :param username, email, password: user data
    :return: True -> user added; IntegityError -> username or email already in DB; HTTPExcepion
    """
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
        query = query.where(UserModel.primary_key == user_id)
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


async def add_new_house(db_session: AsyncSession, user_id: int, house_name: str):
    stmt = insert(HouseModel).values(name = house_name, user_id = user_id)
    try:
        await db_session.execute(stmt)
        await db_session.commit()
        stmt = select(HouseModel).where(HouseModel.user_id == user_id, HouseModel.name == house_name)
        res = await db_session.execute(stmt)
        house = res.scalars().one()
        _logger.info(f"ADD HOUSE_ID {house.primary_key}")
        return house
    except IntegrityError as e:
        await db_session.rollback()
        raise HTTPException(status_code=400, detail="House Name already exists")
    except Exception as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

async def delete_house(db_session: AsyncSession, house_id):
    try:
        # stmt = delete(RoomModel).where(RoomModel.house_id == house_id)
        stmt = delete(HouseModel).where(HouseModel.primary_key == house_id)
        await db_session.execute(stmt)
        await db_session.commit()
        return True
    except IntegrityError as e:
        _logger.error(e)
        raise HTTPException(status_code=400, detail='Cannot delete house')
    except Exception as e:
        _logger.error(e)
        raise e

async def get_houses_on_user(db_session: AsyncSession, user_id: int):
    try:
        # stmt = select(HouseModel).where(HouseModel.user_id == user_id)
        # res = await db_session.execute(stmt)
        # return res.scalars().all()
        stmt = (
            select(HouseModel)
            .options(
                joinedload(HouseModel.rooms)
                .joinedload(RoomModel.devices)
                .joinedload(RoomDeviceModel.device)
                .joinedload(DeviceModel.dev_rooms)
            )
            .filter(HouseModel.user_id == user_id)
        )
        # print(str(stmt))
        houses = await db_session.execute(stmt)
        houses = houses.scalars().unique().all()
        return houses
    except NoResultFound:
        _logger.error(f'U_ID {user_id} NO HOUSE FOUND')
        raise HTTPException(status_code=404, detail='NO HOUSE FOUND')
    except Exception as e:
        _logger.error(e)
        raise e
    
async def get_house_by_room(db_session: AsyncSession, room_id: int):
    try:
        stmt = select(HouseModel.primary_key).join(RoomModel, RoomModel.house_id == HouseModel.primary_key).where(RoomModel.primary_key == room_id)
        print(str(stmt))
        res = await db_session.execute(stmt)
        return res.scalar_one_or_none()
    except NoResultFound:
        raise HTTPException(400, 'NOT FOUND')

async def verify_house_owner(db_session: AsyncSession, user_id: int, house_id: int):
    try:
        stmt = select(HouseModel).where(HouseModel.primary_key == house_id, HouseModel.user_id == user_id)
        res = await db_session.execute(stmt)
        return res
    except NoResultFound:
        return None
    except Exception as e:
        _logger.error(e)
        return HTTPException(400, e)

async def add_new_room(db_session: AsyncSession, house_id: int, room_name: str):
    try:
        unique = await verify_unique_room(db_session, house_id, room_name)
        if unique:
            stmt = insert(RoomModel).values(house_id=house_id, name=room_name)
            await db_session.execute(stmt)
            await db_session.commit()
            _logger.info(f"ADD ROOM_NAME {room_name} HOUSE_ID {house_id}")
            return True
        else:
            raise HTTPException(status_code=400, detail=f"Room with name {room_name} already exists.\nPlease choose other name for this room.")
    except Exception as e:
        _logger.error(e)
        await db_session.rollback()
        raise e
    
async def delete_room(db_session: AsyncSession, room_id: int):
    try:
        stmt = delete(RoomModel).where(RoomModel.primary_key == room_id)
        await db_session.execute(stmt)
        await db_session.commit()
        return True
    except IntegrityError as e:
        _logger.error(e)
        raise HTTPException(status_code=400, detail='Cannot delete room')
    except Exception as e:
        _logger.error(e)
        raise e
    
async def add_new_device(db_session: AsyncSession, user_id: int, device_data):
    try:
        if device_data.dev_id is None or device_data.name is None or user_id is None:
            return False
        # new_dev = DeviceModel(
        #     dev_id = device_data.dev_id,
        #     name = device_data.name,
        #     user_id = user_id,
        #     description = device_data.description
        # )
        # await db_session.add(new_dev)
        stmt = insert(DeviceModel).values(
            dev_id = device_data.dev_id,
            name = device_data.name,
            user_id = user_id,
            description = device_data.description
            )
        await db_session.execute(stmt)
        await db_session.commit()
        return True
    except SQLAlchemyError as e:
        await db_session.rollback()
        _logger(f"SQLAlchemyError: {e}")
        return False
    except IntegrityError:
        await db_session.rollback()
        _logger.error(f"IntegrityError: {e.orig}")
        return False
    except Exception as e:
        await db_session.rollback()
        _logger.error(e)
        return False
    
async def add_room_device(db_session: AsyncSession, device_primary, room_id):
    try:
        # rd = RoomDeviceModel(room_id = room_id, device_id = device_id)
        # await db_session.add(rd)
        stmt = insert(RoomDeviceModel).values(room_id = room_id, device_primary = device_primary)
        await db_session.execute(stmt)
        await db_session.commit()
        _logger.info(f'DEV_ID {device_primary} ADDED TO ROOM_ID {room_id}')
        return True
    except IntegrityError as e:
        await db_session.rollback()
        _logger.error(f"IntegrityError: {e.orig}")
        return False
    except SQLAlchemyError as e:
        await db_session.rollback()
        _logger(f"SQLAlchemyError: {e}")
        return False
    except Exception as e:
        await db_session.rollback()
        _logger(f"An unexpected error occurred: {e}")
        return False

async def delete_all_devices_in_room(db_session: AsyncSession, room_id: int):
    try:
        stmt = delete(RoomDeviceModel).where(RoomDeviceModel.room_id == room_id)
        await db_session.execute(stmt)
        await db_session.commit()
        return True
    except IntegrityError as e:
        _logger.error(f"IntegrityError occurred: {e}")
        await db_session.rollback()
        return False
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError occurred: {e}")
        await db_session.rollback()
        return False
    except Exception as e:
        _logger.error(f"An unexpected error occurred: {e}")
        await db_session.rollback()
        return False

async def delete_room_device(db_session: AsyncSession, room_id: int, device_primary_key: int):
    try:
        stmt = delete(RoomDeviceModel).where(RoomDeviceModel.room_id == room_id, RoomDeviceModel.device_primary == device_primary_key)
        await db_session.execute(stmt)
        await db_session.commit()
        return True
    except IntegrityError as e:
        _logger.error(f"IntegrityError occurred: {e}")
        await db_session.rollback()
        return False
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError occurred: {e}")
        await db_session.rollback()
        return False
    except Exception as e:
        _logger.error(f"An unexpected error occurred: {e}")
        await db_session.rollback()
        return False
    
async def delete_device(db_session: AsyncSession, device_primary_key: int = None, device_id: str = None):
    try:
        if not device_id and not device_primary_key:
            return False
        stmt = delete(DeviceModel)
        
        if device_primary_key:
            stmt = stmt.where(DeviceModel.primary_key == device_primary_key)
        if device_id:
            stmt = stmt.where(DeviceModel.dev_id == device_id)
        
        await db_session.execute(stmt)
        await db_session.commit()
        return True
    except IntegrityError as e:
        _logger.error(f"IntegrityError occurred: {e}")
        await db_session.rollback()
        return False
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError occurred: {e}")
        await db_session.rollback()
        return False
    except Exception as e:
        _logger.error(f"An unexpected error occurred: {e}")
        await db_session.rollback()
        return False
    
async def get_device(db_session:AsyncSession, user_id: int, primary_key: int = None, dev_id: str = None, name: str = None):
    """
    Get Device data
    :param db_session: AsyncSession to access DB
    :param user_id: Owner of the Sensor
    :param id: Optional; device.primary_key in DB
    :param dev_id: Optional; device.dev_id (Factory ID)
    :param name: OPtional Device Name
    """
    
    if not primary_key and not dev_id and not name:
        return None
    stmt = select(DeviceModel)
    if primary_key:
        stmt = stmt.where(DeviceModel.primary_key == primary_key, DeviceModel.user_id == user_id)
    if dev_id:
        stmt = stmt.where(DeviceModel.dev_id == dev_id, DeviceModel.user_id == user_id)
    if name:
        stmt = stmt.where(DeviceModel.name == name, DeviceModel.user_id == user_id)
    try:
        res = await db_session.execute(stmt)
        return res.scalars().one()
    except NoResultFound:
        return None
    except SQLAlchemyError as e:
        # Handle general SQLAlchemy errors
        _logger.error(f"SQLAlchemyError: {e}")
        raise HTTPException(status_code=500, detail="Database error occurred.")
    except Exception as e:
        _logger.error(e)
        return HTTPException(status_code=500, detail="Unexpected Error")

async def verify_unique_room(db_session:AsyncSession, house_id: int, room_name: str):
    """
    Check if the room with given room_name is already in the house_id
    :param db_session: SQLAlchemy AsyncSession
    :param house_id: ID of the house
    :param room_name: Room name to search for
    """
    # stmt = select(RoomModel).where(RoomModel.house_id == house_id, RoomModel.name == room_name);
    # res = await db_session.execute(stmt)
    # res.scalars().all()
    # return len(res) == 0

    stmt = select(func.count(RoomModel.primary_key)).where(RoomModel.house_id == house_id, RoomModel.name == room_name)
    res = await db_session.execute(stmt)
    return res.scalar() == 0
"""async def update_session_user(db_session: AsyncSession, user_id: int = None, username: str = None, session_id: str = None):
    if not user_id and not username:
        _logger.error("EMPTY SET")
        raise ValueError()
    if not session_id:
        _logger.error("session_id SET inactive")
        session_id = 'inactive'
    query = update(UserModel).values(session_id = session_id)
    if user_id:
        query.where(UserModel.primary_key == user_id)
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
    return user.primary_key, user.name"""