"""
Память пользователя.

Хранит устойчивые факты: марку машины, город, тип жилья и т.п.
НЕ хранит временные события («сегодня сломалась машина»).

По ТЗ (этап 31) — извлекаем только долгосрочные данные.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UserMemory
from app.logging_config import get_logger

logger = get_logger(__name__)


async def upsert_memory(
    session: AsyncSession,
    user_id: int,
    key: str,
    value: str,
    confidence: float = 1.0,
) -> None:
    """Добавить или обновить факт в памяти пользователя."""
    stmt = select(UserMemory).where(
        UserMemory.user_id == user_id,
        UserMemory.key == key,
    )
    result = await session.execute(stmt)
    item = result.scalar_one_or_none()

    if item is None:
        item = UserMemory(
            user_id=user_id,
            key=key,
            value=value,
            confidence=confidence,
        )
        session.add(item)
    else:
        item.value = value
        item.confidence = confidence

    await session.commit()


async def get_memory_dict(
    session: AsyncSession,
    user_id: int,
) -> dict[str, str]:
    stmt = select(UserMemory).where(UserMemory.user_id == user_id)
    result = await session.execute(stmt)
    return {item.key: item.value for item in result.scalars().all()}


async def delete_memory(
    session: AsyncSession,
    user_id: int,
    key: Optional[str] = None,
) -> None:
    """Удалить факт или всю память пользователя."""
    stmt = select(UserMemory).where(UserMemory.user_id == user_id)
    if key is not None:
        stmt = stmt.where(UserMemory.key == key)

    result = await session.execute(stmt)
    for item in result.scalars().all():
        await session.delete(item)
    await session.commit()