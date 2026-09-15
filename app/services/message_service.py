"""
Сервис работы с сообщениями и разговорами.

Управляет:
- созданием conversation;
- поиском активного разговора;
- сохранением user/assistant сообщений;
- обновлением summary после нескольких сообщений.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Conversation, Message
from app.logging_config import get_logger

logger = get_logger(__name__)


# Разговор считается «активным», если последнее сообщение было
# не позднее N минут назад. Иначе начинаем новую conversation.
CONVERSATION_TTL_MINUTES = 30


def make_title(text: str, max_len: int = 60) -> str:
    text = text.strip().replace("\n", " ")
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


async def get_or_create_active_conversation(
    session: AsyncSession,
    user_id: int,
    title: str,
    category: str,
) -> Conversation:
    """
    Вернуть активный разговор или создать новый.

    «Активный» — если последнее сообщение было недавно.
    """
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(minutes=CONVERSATION_TTL_MINUTES)

    stmt = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    conv = result.scalar_one_or_none()

    if conv is not None and conv.updated_at >= threshold:
        # Обновим updated_at (SQLAlchemy сам по onupdate), категорию оставим
        conv.updated_at = now
        await session.commit()
        return conv

    conv = Conversation(user_id=user_id, title=title[:255], category=category)
    session.add(conv)
    await session.commit()
    await session.refresh(conv)
    return conv


async def save_user_message(
    session: AsyncSession,
    conversation_id: int,
    content: str,
    message_type: str = "text",
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=content,
        message_type=message_type,
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg


async def save_assistant_message(
    session: AsyncSession,
    conversation_id: int,
    content: str,
    model: str,
    tokens: int = 0,
    message_type: str = "text",
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=content,
        message_type=message_type,
        model=model,
        tokens=tokens,
    )
    session.add(msg)
    await session.commit()
    await session.refresh(msg)
    return msg