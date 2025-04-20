"""
    Author: O. Baida

    Initialisierung der Datenbank
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import Config
from . import models
from .base import Base

logger = Config.logger_init()
logger.info("START DB")
__all__=["Base", "models"]

async_engine = create_async_engine(Config.SQLALCHEMY_DATABASE_URL)

async_session = sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)

async def create_tables():
    async with async_engine.begin() as connection:
        #await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
        await connection.commit()
        logger.info("TABLES CREATED")

async def get_session():
    async with async_session() as session:
        yield session

async def get_direct_session():
    async with async_session() as session:
        return session
    
async def close_session(session: AsyncSession):
    await session.close()