from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine, 
    AsyncSession, 
    async_sessionmaker, 
    create_async_engine
)
from sqlalchemy.orm import DeclarativeBase

from app.config import Config

# Все таблицы наследуются от Base, и SQLAlchemy собирает метаданные.
class Base(DeclarativeBase):
    pass


def make_engine(cfg: Config):
    # engine = объект соединения с БД (не сама сессия)
    # echo=False — не печатаем все SQL запросы в консоль
    return create_async_engine(cfg.database_url, echo=False)


def make_sessionmaker(engine: AsyncEngine):
    return async_sessionmaker(engine, expire_on_commit=False)


async def init_db(engine: AsyncEngine) -> None:
    from app import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)