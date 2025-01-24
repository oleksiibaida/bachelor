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
        await connection.run_sync(Base.metadata.create_all)
        await connection.commit()
        logger.debug("TABLES CREATED")

async def get_session():
    async with async_session() as session:
        yield session

# async def init_db():
#     logger.info(msg=f"START")
#     async with async_engine.begin() as connection:
#         await connection.run_sync(Base.metadata.create_all())
        
"""
@app.teardown_appcontext
def teardown_app(error):
    db_session.remove()
    if error is not None:
        _logger.error(msg=error)
"""