"""
Основной обработчик текстовых сообщений.

Полный конвейер:
    пользователь
      ↓
    найти/создать пользователя
      ↓
    найти/создать активный разговор
      ↓
    Router (категория)
      ↓
    Context (memory + summary + последние сообщения)
      ↓
    PromptBuilder
      ↓
    YandexGPT
      ↓
    Validator
      ↓
    Formatter
      ↓
    сохранить user/assistant
      ↓
    отправить
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.ai.context import build_context
from app.ai.formatter import format_answer
from app.ai.prompt_builder import build_system_prompt, build_user_message
from app.ai.router import route_message
from app.ai.validator import get_structured_answer
from app.ai.yandexgpt import get_yandex_client
from app.bot.keyboards.response import (
    after_answer_keyboard,
    main_menu_after_answer,
)
from app.bot.states.user_states import UserFlow
from app.database.database import AsyncSessionLocal
from app.database.repository import get_or_create_user
from app.services.message_service import (
    get_or_create_active_conversation,
    make_title,
    save_assistant_message,
    save_user_message,
)
from app.logging_config import get_logger

router = Router(name="message")
logger = get_logger(__name__)


@router.message(UserFlow.waiting_for_question, F.text)
async def on_question(message: Message, state: FSMContext) -> None:
    await state.clear()

    tg_user = message.from_user
    user_text = (message.text or "").strip()

    if tg_user is None or not user_text:
        await message.answer("Не удалось разобрать сообщение. Попробуйте ещё раз.")
        return

    yandex = get_yandex_client()
    if not yandex.configured:
        logger.warning("YandexGPT не настроен — работаем без AI")
        await message.answer(
            "🤖 Разбор ситуаций ещё не подключён. "
            "Скоро всё заработает — спасибо за терпение!"
        )
        return

    await message.bot.send_chat_action(message.chat.id, "typing")

    # Router (локально + при необходимости через AI)
    route = await route_message(user_text, client=yandex)
    logger.info("Категория: %s (source=%s)", route.category, route.source)

    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            language=tg_user.language_code or "ru",
        )

        # Активный разговор
        conv = await get_or_create_active_conversation(
            session,
            user_id=user.id,
            title=make_title(user_text),
            category=route.category,
        )

        # Сообщение пользователя
        await save_user_message(session, conv.id, user_text, "text")

        # Контекст
        ctx = await build_context(session, user_id=user.id, conversation_id=conv.id)

        # Промпт
        system_prompt = build_system_prompt(route.category)
        user_message = build_user_message(
            user_text=user_text,
            memory=ctx["memory"],
            summary=ctx["summary"],
            history=ctx["history"],
        )

        # AI
        answer = await get_structured_answer(
            client=yandex,
            system_prompt=system_prompt,
            user_message=user_message,
        )

        formatted = format_answer(answer)

        # Сохраняем ответ ассистента
        await save_assistant_message(
            session,
            conversation_id=conv.id,
            content=formatted,
            model=answer.model or yandex.model_name,
            tokens=answer.tokens_total,
            message_type="text",
        )

        conv_id = conv.id

    logger.info("Ответ сформирован (conv_id=%s, tokens=%s)",
                conv_id, answer.tokens_total)

    try:
        await message.answer(formatted, reply_markup=after_answer_keyboard())
    except Exception as exc:
        logger.error("Не удалось отправить ответ: %s", exc)
        await message.answer(
            "Произошла ошибка при отправке ответа. Попробуйте ещё раз."
        )
        return

    await message.answer("Что дальше?", reply_markup=main_menu_after_answer())


@router.message(F.text)
async def on_any_text(message: Message, state: FSMContext) -> None:
    if message.text and message.text.startswith("/"):
        return
    await message.answer(
        "Нажмите «🤖 Разобраться», если хотите описать ситуацию."
    )