"""
Основной обработчик текстовых сообщений.

На этом этапе:
- регистрируем пользователя;
- отвечаем заглушкой.

В этапе 4 здесь появится вызов YandexGPT.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.states.user_states import UserFlow
from app.database.database import AsyncSessionLocal
from app.database.repository import get_or_create_user
from app.logging_config import get_logger

router = Router(name="message")
logger = get_logger(__name__)


@router.message(UserFlow.waiting_for_question, F.text)
async def on_question(message: Message, state: FSMContext) -> None:
    """
    Пользователь нажал «🤖 Разобраться» и написал вопрос.
    Пока просто подтверждаем получение — логика AI будет в этапе 4.
    """
    await state.clear()

    tg_user = message.from_user
    if tg_user is not None:
        async with AsyncSessionLocal() as session:
            await get_or_create_user(
                session,
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                language=tg_user.language_code or "ru",
            )

    logger.info(
        "Получен вопрос от telegram_id=%s, длина=%s",
        tg_user.id if tg_user else None,
        len(message.text or ""),
    )

    await message.answer(
        "👌 Принял вашу ситуацию.\n\n"
        "Сейчас я ещё учусь разбирать такие случаи — "
        "полноценные ответы появятся в следующих обновлениях."
    )


@router.message(F.text)
async def on_any_text(message: Message, state: FSMContext) -> None:
    """
    Любой текст вне сценария — мягко возвращаем в меню.
    Не отвечаем на команды (их ловят более ранние роутеры).
    """
    if message.text and message.text.startswith("/"):
        return

    await message.answer(
        "Нажмите «🤖 Разобраться», если хотите описать ситуацию."
    )