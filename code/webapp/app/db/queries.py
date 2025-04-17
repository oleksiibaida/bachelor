import bcrypt
from app.config import Config
from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.exc import IntegrityError, NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from .models import UserModel, HouseModel, RoomModel, DeviceModel, RoomDeviceModel, ScenarioModel
from fastapi import Depends, HTTPException

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
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        new_user = UserModel(username=username, email=email, password=password_hash)
        _logger.debug(f'ADD U_NAME {new_user.username} START')
        db_session.add(new_user)
        await db_session.commit()
        await db_session.refresh(new_user)
        _logger.debug(f'ADD U_NAME {new_user.username} COMPLETED')
        return new_user.primary_key
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="ALREADY EXISTS")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")

async def get_user_data(db_session: AsyncSession, user_primary: int = None, username: str = None, email: str = None):
    if not user_primary and not username and not email:
        _logger.error(msg="EMPTY SET")
        raise ValueError()
    query = select(UserModel)
    if user_primary:
        query = query.where(UserModel.primary_key == user_primary)
    if username:
        query = query.where(UserModel.username == username)
    if email:
        query = query.where(UserModel.email == email)
    try:
        res = await db_session.execute(query)
        return res.scalars().first()
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")

async def add_new_house(db_session: AsyncSession, user_primary: int, house_name: str):
    try:
        new_house = HouseModel(user_id=user_primary, name=house_name)
        db_session.add(new_house)
        await db_session.commit()
        await db_session.refresh(new_house)
        _logger.info(f"U_ID: {user_primary} ADD HOUSE_ID {new_house.primary_key}")
        return new_house
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="ALREADY EXISTS")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")

async def delete_house(db_session: AsyncSession, house_id):
    try:
        house = await db_session.get(HouseModel, house_id)
        await db_session.delete(house)
        await db_session.commit()
        return True
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")

async def get_house(db_session: AsyncSession, house_primary: int):
    try:
        return await db_session.get(HouseModel, house_primary)
    except NoResultFound:
        _logger.error(f'HOUSE_ID {house_primary} HOUSE NOT FOUND')
        raise HTTPException(status_code=404, detail='NOT FOUND')
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")

async def get_houses_on_user(db_session: AsyncSession, user_primary: int):
    try:
        stmt = (
            select(HouseModel)
            .options(
                joinedload(HouseModel.rooms)
                .joinedload(RoomModel.devices)
                .joinedload(RoomDeviceModel.device)
                .joinedload(DeviceModel.dev_rooms)
            )
            .filter(HouseModel.user_id == user_primary)
        )
        # print(str(stmt))
        houses = await db_session.execute(stmt)
        houses = houses.scalars().unique().all()
        return houses
    except NoResultFound:
        _logger.error(f'U_ID {user_primary} HOUSE NOT FOUND')
        raise HTTPException(status_code=404, detail='NOT FOUND')
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")
    
async def get_house_by_room(db_session: AsyncSession, room_id: int):
    try:
        stmt = select(HouseModel).join(RoomModel, RoomModel.house_id == HouseModel.primary_key).where(RoomModel.primary_key == room_id)
        res = await db_session.execute(stmt)
        return res.scalar_one_or_none()
    except NoResultFound as e:
        _logger.error(f"NoResultFound:{e}")
        raise HTTPException(404, 'NOT FOUND')
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")
    
async def verify_house_owner(db_session: AsyncSession, user_primary: int, house_id: int):
    try:
        house = await db_session.get(HouseModel, house_id)
        if house:
            return house.user_id == user_primary
    except NoResultFound as e:
        _logger.error(f"NoResultFound: {e}")
        raise HTTPException(404, 'NOT FOUND')
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")

async def add_new_room(db_session: AsyncSession, house_id: int, room_name: str):
    try:
        new_room = RoomModel(name = room_name, house_id = house_id)
        db_session.add(new_room)
        await db_session.commit()
        await db_session.refresh(new_room)
        _logger.info(f"ADD ROOM_NAME {room_name} HOUSE_ID {house_id}")
        return new_room
    except NoResultFound as e:
        _logger.error(f"NoResultFound:{e}")
        raise HTTPException(404, 'NOT FOUND')
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="ALREADY EXISTS")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")

async def delete_room(db_session: AsyncSession, room_id: int):
    try:
        # get RoomModel from DB
        del_room = await db_session.execute(
            select(RoomModel)
            .where(RoomModel.primary_key == room_id)
        )
        # fetch result
        del_room = del_room.scalars().one()

        await db_session.delete(del_room)
        await db_session.commit()
        return True
    except NoResultFound as e:
        _logger.error(f"NoResultFound:{e}")
        raise HTTPException(404, 'NOT FOUND')
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"An unexpected error: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")
    
async def add_new_device(db_session: AsyncSession, user_id: int, device_data):
    try:
        if device_data.dev_id is None or device_data.name is None or user_id is None:
            return False
        # print(DeviceModel.__table__.columns.keys())
        new_dev = DeviceModel(
            dev_id = device_data.dev_id,
            name = device_data.name,
            user_id = user_id,
            description = device_data.description
        )
        db_session.add(new_dev)
        await db_session.commit()
        await db_session.refresh(new_dev)
        return new_dev
    except NoResultFound as e:
        _logger.error(f"NoResultFound:{e}")
        raise HTTPException(404, 'NOT FOUND')
    except IntegrityError as e:
        await db_session.rollback()
        _logger.error(f"IntegrityError: {e}")
        raise HTTPException(status_code=422, detail="ALREADY EXISTS")
    except SQLAlchemyError as e:
        await db_session.rollback()
        _logger.error(f"SQLAlchemyError: {e}")
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        await db_session.rollback()
        _logger.error(f"An unexpected error: {e}")
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    
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
        return res.scalar_one_or_none()
    except NoResultFound:
        return None
    except IntegrityError as e:
        await db_session.rollback()
        _logger.error(f"IntegrityError: {e.orig}")
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        await db_session.rollback()
        _logger.error(f"SQLAlchemyError: {e}")
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        await db_session.rollback()
        _logger.error(f"An unexpected error: {e}")
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")
    
async def get_devices_on_user(db_session: AsyncSession, user_primary: int):
    try:
        stmt = (
            select(DeviceModel)
            .options(
                joinedload(DeviceModel.dev_rooms)
                .joinedload(RoomDeviceModel.room)
                .joinedload(RoomModel.devices)
            )
            .filter(DeviceModel.user_id == user_primary)
        )        
        
        devices = await db_session.execute(stmt)
        return devices.scalars().unique().all()
    except NoResultFound:
        _logger.error(f'U_ID {user_primary} HOUSE NOT FOUND')
        raise HTTPException(status_code=404, detail='NOT FOUND')
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")
    
async def verify_user_device(db_session: AsyncSession, user_id: int, device_id):
    try:
        stmt = select(DeviceModel).where(DeviceModel.dev_id == device_id, DeviceModel.user_id == user_id)
        res = await db_session.execute(stmt)
        return res.scalars().one_or_none()
    except NoResultFound:
        _logger.error(f' U_ID {user_id} IS NOT OWNER OF DEV_ID {device_id}')
        raise HTTPException(status_code=404, detail=f'U_ID {user_id} IS NOT OWNER OF DEV_ID {device_id}')
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except HTTPException as e:
        raise e
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")

async def update_device(db_session: AsyncSession, user_id:int, new_device_data):
    try:
        if new_device_data.dev_id is None:
            _logger.error("DEV_ID IS NOT PROVIDED")
            raise HTTPException(status_code=400, detail="DEV_ID IS NOT PROVIDED")
        if new_device_data.length < 1:
            _logger.error("NEW DATA IS NOT PROVIDED")
            raise HTTPException(status_code=400, detail="NEW DATA IS NOT PROVIDED")
        # device = await db_session.get(DeviceModel, new_device_data.primary)
        find_device_stmt = select(DeviceModel).where(DeviceModel.user_id == user_id, DeviceModel.dev_id == new_device_data.dev_id)
        res = await db_session.execute(find_device_stmt)
        device = res.scalars().one()
        if device:
            if device.user_id != user_id:
                _logger.critical(f"UNAUTHORIZED ACCESS U_ID {user_id} ON DEVICE {device.primary_key}")
                raise HTTPException(status_code=401, detail="User is not owner of this device")
            if new_device_data.name:
                device.name = new_device_data.name
            if new_device_data.description:
                device.description = new_device_data.description
            await db_session.commit()
        return device
    except NoResultFound:
        _logger.error(f'{new_device_data.primary} DEVICE NOT FOUND')
        raise HTTPException(status_code=404, detail='NOT FOUND')
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except HTTPException as e:
        raise e
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")
    
async def update_device_handshake_data(db_session: AsyncSession, device_id, handshake_data):
    try:
        # Convert handshake_data in .csv format
        data_fields_csv = ','.join(handshake_data.get("data_fields")) if handshake_data.get("data_fields") is not None else None
        commands_csv = ','.join(handshake_data.get("commands")) if handshake_data.get("commands") is not None else None
        stmt = (
            update(DeviceModel)
            .where(DeviceModel.dev_id == device_id)
            .values(
                data_fields = data_fields_csv,
                commands = commands_csv
            )
        )
        await db_session.execute(stmt)
        await db_session.commit()
        return
    except NoResultFound:
        _logger.error(f'{handshake_data.dev_id} DEVICE NOT FOUND')
        raise HTTPException(status_code=404, detail='NOT FOUND')
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except HTTPException as e:
        raise e
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")
    
async def delete_device(db_session: AsyncSession, device_primary_key: int, device_id: str = None):
    try:
        if not device_id and not device_primary_key:
            _logger.error("EMPTY SET")
            raise HTTPException(status_code=400, detail="NO DEVICE DATA PROVIDED")
        # del_device = DeviceModel(primary_key = device_primary_key, dev_id = device_id)
        del_device = await db_session.get(DeviceModel, device_primary_key)
        if del_device:
            await db_session.delete(del_device)
            await db_session.commit()
            return True
        else:
            raise HTTPException(404, 'NOT FOUND')
    except NoResultFound as e:
        _logger.error(f"NoResultFound:{e}")
        raise HTTPException(404, 'NOT FOUND')
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"An unexpected error: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")
    
async def add_room_device(db_session: AsyncSession, device_primary, room_id):
    try:
        rd = RoomDeviceModel(room_id = room_id, device_primary = device_primary)
        db_session.add(rd)
        await db_session.commit()
        _logger.info(f'DEV_ID {device_primary} ADDED TO ROOM_ID {room_id}')
        return True
    except IntegrityError as e:
        await db_session.rollback()
        _logger.error(f"IntegrityError: {e.orig}")
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        await db_session.rollback()
        _logger.error(f"SQLAlchemyError: {e}")
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        await db_session.rollback()
        _logger.error(f"An unexpected error: {e}")
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")

async def delete_room_device(db_session: AsyncSession, room_id: int, device_primary_key: int):
    try:
        # get room_device from DB
        del_rd = await db_session.execute(
            select(RoomDeviceModel).where(
                RoomDeviceModel.room_id==room_id,
                RoomDeviceModel.device_primary==device_primary_key
            )
        )
        del_rd = del_rd.scalars().first()
        if del_rd:
            await db_session.delete(del_rd)
            await db_session.commit()
            return True
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except IntegrityError as e:
        await db_session.rollback()
        _logger.error(f"IntegrityError: {e.orig}")
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        await db_session.rollback()
        _logger.error(f"SQLAlchemyError: {e}")
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        await db_session.rollback()
        _logger.error(f"An unexpected error: {e}")
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")
    

async def add_scenario(db_session: AsyncSession, user_id: int, name: str, source_dev: str, data_field: str, condition: ScenarioModel.ScenarioConditionsEnum, value: str, target_dev: str, command: str):
    try:
        if not condition in [k.value for k in ScenarioModel.ScenarioConditionsEnum]:
            return HTTPException(status_code=422, detail="Condition has wrong value")
        enum_condition = ScenarioModel.ScenarioConditionsEnum(condition)
        new_scenario = ScenarioModel(
            user_id = user_id,
            name = name,
            source_dev = source_dev,
            data_field = data_field.lower(),
            condition = enum_condition,
            value = value,
            target_dev = target_dev,
            command = command
        )
        db_session.add(new_scenario)
        await db_session.commit()
        return new_scenario
    except IntegrityError as e:
        await db_session.rollback()
        _logger.error(f"IntegrityError: {e.orig}")
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        await db_session.rollback()
        _logger.error(f"SQLAlchemyError: {e}")
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        await db_session.rollback()
        _logger.error(f"An unexpected error: {e}")
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")
    
async def get_all_scenarios(db_session: AsyncSession):
    try:
        res = await db_session.execute(select(ScenarioModel))
        return res.scalars().all()
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")

async def get_scenarios_on_user(db_session:AsyncSession, user_id: int):
    try:
        stmt = select(ScenarioModel).where(ScenarioModel.user_id == user_id)
        res = await db_session.execute(stmt)
        return res.scalars().all()
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")
    
async def get_scenarios_for_device(db_session: AsyncSession, device_id):
    try:
        stmt = select(ScenarioModel).where(ScenarioModel.target_dev == device_id)
    except IntegrityError as e:
        _logger.error(f"IntegrityError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        _logger.error(f"SQLAlchemyError: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        _logger.error(f"Exception: {e}")
        await db_session.rollback()
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")
    
def get_scenario_conditions():
    return [e.value for e in ScenarioModel.ScenarioConditionsEnum]

async def delete_scenario(db_session: AsyncSession, scenario_primary: int):
    try:
        del_scenario = await db_session.get(ScenarioModel, scenario_primary)
        if del_scenario:
            await db_session.delete(del_scenario)
            await db_session.commit()
            return True
        return False
    except IntegrityError as e:
        await db_session.rollback()
        _logger.error(f"IntegrityError: {e.orig}")
        raise HTTPException(status_code=422, detail="NOT FOUND")
    except SQLAlchemyError as e:
        await db_session.rollback()
        _logger.error(f"SQLAlchemyError: {e}")
        raise HTTPException(status_code=500, detail="DATABASE ERROR")
    except Exception as e:
        await db_session.rollback()
        _logger.error(f"An unexpected error: {e}")
        raise HTTPException(status_code=500, detail="UNEXPECTED DATABASE ERROR")