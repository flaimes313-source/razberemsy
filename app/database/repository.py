"""
Репозиторий — тонкий слой между сервисами и SQLAlchemy-моделями.

Здесь только простые CRUD-операции, без бизнес-логики.
Бизнес-логика — в services/.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User


# ============================================================
# users
# ============================================================
async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    language: str = "ru",
) -> User:
    user = User(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        language=language,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_or_create_user(
    session: AsyncSession,
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    language: str = "ru",
) -> User:
    user = await get_user_by_telegram_id(session, telegram_id)
    if user is None:
        user = await create_user(
            session,
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            language=language,
        )
        return user

    # Обновим актуальные данные и last_active_at
    changed = False
    if username is not None and user.username != username:
        user.username = username
        changed = True
    if first_name is not None and user.first_name != first_name:
        user.first_name = first_name
        changed = True

    user.last_active_at = datetime.now(timezone.utc)
    changed = True

    if changed:
        await session.commit()
        await session.refresh(user)

    return user