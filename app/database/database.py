"""
Подключение к PostgreSQL через SQLAlchemy 2.x (async).

Схема:
    DATABASE_URL из .env
        ↓
    create_async_engine
        ↓
    async_sessionmaker
        ↓
    Base (declarative base для моделей)
"""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""
    pass


# Движок создаём один раз на всё приложение.
# pool_pre_ping=True — переподключение, если соединение «упало».
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    future=True,
)

# Фабрика сессий.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI-совместимый генератор сессий."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """
    Создать таблицы, если их нет.

    На MVP используется Base.metadata.create_all.
    После появления реальных данных структуру БД меняем
    контролируемо (SQL-миграции вручную или Alembic позже).
    """
    # Импорт нужен, чтобы модели зарегистрировались в metadata.
    from app.database import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Таблицы БД проверены/созданы.")


async def close_db() -> None:
    """Корректно закрыть пул соединений при остановке приложения."""
    await engine.dispose()
    logger.info("Соединения с БД закрыты.")