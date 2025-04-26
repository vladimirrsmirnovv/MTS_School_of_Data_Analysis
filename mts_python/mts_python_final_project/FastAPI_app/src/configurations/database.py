import logging

from typing import AsyncGenerator, Callable, Optional
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.models.base import BaseModel
from src.configurations.settings import settings

__all__ = ["global_init", "get_async_session", "create_db_and_tables"]

logger = logging.getLogger("__name__")

__async_engine: Optional[AsyncEngine] = None
__session_factory: Optional[Callable[[], AsyncSession]] = None

SQLALCHEMY_DATABASE_URL = settings.database_url


def global_init() -> None:
    global __async_engine, __session_factory

    if __session_factory:
        return

    if not __async_engine:
        __async_engine = create_async_engine(url=SQLALCHEMY_DATABASE_URL, echo=True)

    __session_factory = async_sessionmaker(__async_engine)


async def get_async_session() -> AsyncGenerator:
    global __session_factory

    if not __session_factory:
        raise ValueError(
            {"message": "You must call global_init() before using this method"}
        )

    session: AsyncSession = __session_factory()

    try:
        yield session
        await session.commit()
    except Exception as e:
        logger.error("Raises exception: %s", e)
        raise e
    finally:
        await session.rollback()
        await session.close()


async def create_db_and_tables():
    # from src.models.books import Book

    global __async_engine

    if __async_engine is None:
        raise ValueError(
            {"message": "You must call global_init() before using this method"}
        )

    async with __async_engine.begin() as conn:
        # await conn.run_sync(BaseModel.metadata.drop_all)
        await conn.run_sync(BaseModel.metadata.create_all)
