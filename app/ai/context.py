"""
Контекст разговора.

Собирает:
- последние N сообщений (по ТЗ — 3–5);
- summary разговора;
- память пользователя (устойчивые факты).

Не отправляем всю историю — это дорого.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Conversation, Message, UserMemory


# Сколько последних сообщений отправляем в AI
LAST_MESSAGES_LIMIT = 5


async def get_last_messages(
    session: AsyncSession,
    conversation_id: int,
    limit: int = LAST_MESSAGES_LIMIT,
) -> list[dict[str, str]]:
    """
    Вернуть последние `limit` сообщений разговора.

    Порядок — от старых к новым (как удобно для промпта).
    """
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.id.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = list(result.scalars().all())
    rows.reverse()
    return [
        {"role": row.role, "content": row.content}
        for row in rows
    ]


async def get_conversation_summary(
    session: AsyncSession,
    conversation_id: int,
) -> Optional[str]:
    stmt = select(Conversation.summary).where(Conversation.id == conversation_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_memory(
    session: AsyncSession,
    user_id: int,
) -> dict[str, str]:
    """Словарь устойчивых фактов о пользователе (key → value)."""
    stmt = select(UserMemory).where(UserMemory.user_id == user_id)
    result = await session.execute(stmt)
    items = result.scalars().all()
    return {item.key: item.value for item in items}


async def build_context(
    session: AsyncSession,
    user_id: int,
    conversation_id: Optional[int],
) -> dict:
    """
    Собрать полный контекст для prompt_builder.

    Возвращает:
        {
            "memory": {...},
            "summary": "...",
            "history": [{"role": "...", "content": "..."}],
        }
    """
    memory = await get_user_memory(session, user_id)

    summary: Optional[str] = None
    history: list[dict[str, str]] = []

    if conversation_id is not None:
        summary = await get_conversation_summary(session, conversation_id)
        history = await get_last_messages(session, conversation_id)

    return {
        "memory": memory,
        "summary": summary,
        "history": history,
    }