"""
Основной обработчик текстовых сообщений.

Полный конвейер (по ТЗ):
    пользователь
      ↓
    найти/создать пользователя
      ↓
    (лимиты — появятся на этапе 13)
      ↓
    создать conversation
      ↓
    Router
      ↓
    PromptBuilder
      ↓
    YandexGPT
      ↓
    Validator
      ↓
    Formatter
      ↓
    сохранить запрос/ответ
      ↓
    отправить
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.ai.prompt_builder import build_system_prompt, build_user_message
from app.ai.router import route_message
from app.ai.validator import get_structured_answer
from app.ai.formatter import format_answer
from app.ai.yandexgpt import get_yandex_client
from app.bot.keyboards.response import (
    after_answer_keyboard,
    main_menu_after_answer,
)
from app.bot.states.user_states import UserFlow
from app.database.database import AsyncSessionLocal
from app.database.models import Conversation, Message as MessageModel
from app.database.repository import get_or_create_user
from app.logging_config import get_logger

router = Router(name="message")
logger = get_logger(__name__)


# ------------------------------------------------------------
# Помощники для работы с БД
# ------------------------------------------------------------
async def _save_user_message(
    user_id: int,
    user_text: str,
    category: str,
    title: str,
) -> tuple[int, int]:
    """
    Создать conversation (если нет) + сохранить сообщение пользователя.

    Возвращает (conversation_id, message_id).
    """
    async with AsyncSessionLocal() as session:
        conv = Conversation(
            user_id=user_id,
            title=title[:255],
            category=category,
        )
        session.add(conv)
        await session.commit()
        await session.refresh(conv)

        msg = MessageModel(
            conversation_id=conv.id,
            role="user",
            content=user_text,
            message_type="text",
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)

        return conv.id, msg.id


async def _save_assistant_message(
    conversation_id: int,
    content: str,
    model: str,
) -> int:
    async with AsyncSessionLocal() as session:
        msg = MessageModel(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            message_type="text",
            model=model,
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        return msg.id


def _make_title(text: str, max_len: int = 60) -> str:
    text = text.strip().replace("\n", " ")
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


# ------------------------------------------------------------
# Основной обработчик
# ------------------------------------------------------------
@router.message(UserFlow.waiting_for_question, F.text)
async def on_question(message: Message, state: FSMContext) -> None:
    await state.clear()

    tg_user = message.from_user
    user_text = (message.text or "").strip()

    if tg_user is None or not user_text:
        await message.answer("Не удалось разобрать сообщение. Попробуйте ещё раз.")
        return

    # 1. Пользователь
    async with AsyncSessionLocal() as session:
        user = await get_or_create_user(
            session,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            language=tg_user.language_code or "ru",
        )
        user_db_id = user.id

    # 2. Если YandexGPT не настроен — честно сообщаем
    yandex = get_yandex_client()
    if not yandex.configured:
        logger.warning("YandexGPT не настроен — работаем без AI")
        await message.answer(
            "🤖 Разбор ситуаций ещё не подключён. "
            "Скоро всё заработает — спасибо за терпение!"
        )
        return

    # 3. Что-то вроде "печатает…" — необязательно
    await message.bot.send_chat_action(message.chat.id, "typing")

    # 4. Router
    route = await route_message(user_text, client=yandex)
    logger.info("Категория: %s (source=%s)", route.category, route.source)

    # 5. Сохраняем сообщение пользователя
    conv_id, _ = await _save_user_message(
        user_id=user_db_id,
        user_text=user_text,
        category=route.category,
        title=_make_title(user_text),
    )

    # 6. Собираем промпт
    system_prompt = build_system_prompt(route.category)
    user_message = build_user_message(user_text)

    # 7. Запрос к AI + JSON-парсинг с ретраем
    answer = await get_structured_answer(
        client=yandex,
        system_prompt=system_prompt,
        user_message=user_message,
    )

    # 8. Форматирование
    formatted = format_answer(answer)

    # 9. Сохраняем ответ ассистента
    await _save_assistant_message(
        conversation_id=conv_id,
        content=formatted,
        model=yandex._model if hasattr(yandex, "_model") else "yandexgpt",
    )

    # 10. Отправляем
    try:
        await message.answer(
            formatted,
            reply_markup=after_answer_keyboard(),
        )
    except Exception as exc:
        logger.error("Не удалось отправить ответ: %s", exc)
        await message.answer(
            "Произошла ошибка при отправке ответа. Попробуйте ещё раз."
        )
        return

    # 11. Возвращаем меню
    await message.answer(
        "Что дальше?",
        reply_markup=main_menu_after_answer(),
    )


# ------------------------------------------------------------
# Любой другой текст вне сценария
# ------------------------------------------------------------
@router.message(F.text)
async def on_any_text(message: Message, state: FSMContext) -> None:
    if message.text and message.text.startswith("/"):
        return
    await message.answer(
        "Нажмите «🤖 Разобраться», если хотите описать ситуацию."
    )