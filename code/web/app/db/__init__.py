from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import Config
from . import models
from .base import Base

logger = Config.logger_init()



__all__=["Base", "models"]

async_engine = create_async_engine(Config.SQLALCHEMY_DATABASE_URI)

async_session = sessionmaker(
    async_engine, expire_on_commit=False, class_=AsyncSession
)

async def db_connection():
    async with async_session() as session:
        yield session

async def init_db():
    logger.info(msg=f"START")
    async with async_engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all())
"""
@app.teardown_appcontext
def teardown_app(error):
    db_session.remove()
    if error is not None:
        _logger.error(msg=error)
"""