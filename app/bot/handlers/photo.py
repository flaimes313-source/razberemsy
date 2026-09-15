"""
Обработчик фотографий.

Пользователь может:
- нажать кнопку «📸 Фото» и отправить фото;
- отправить фото напрямую без нажатия кнопки.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.ai.formatter import format_answer
from app.ai.prompt_builder import build_system_prompt, build_user_message
from app.ai.validator import get_structured_answer
from app.ai.yandexgpt import get_yandex_client
from app.bot.keyboards.response import (
    after_answer_keyboard,
    main_menu_after_answer,
)
from app.database.database import AsyncSessionLocal
from app.database.repository import get_or_create_user
from app.services.message_service import (
    get_or_create_active_conversation,
    save_assistant_message,
    save_user_message,
)
from app.services.photo_service import ocr_available, recognize_text
from app.utils.files import download_telegram_file, safe_delete
from app.logging_config import get_logger

router = Router(name="photo")
logger = get_logger(__name__)


PHOTO_SYSTEM_ADDON = (
    "Пользователь прислал фото или скриншот. "
    "Текст с фото распознан и приведён ниже. "
    "Если распознанный текст выглядит как сообщение, документ, "
    "чек или переписка — разберись, что это, и что делать пользователю. "
    "Если текста на фото по смыслу мало — вежливо скажи, что не хватает "
    "информации, и предложи прислать фото лучшего качества или "
    "описать ситуацию словами."
)


@router.message(F.photo)
async def on_photo(message: Message, state: FSMContext) -> None:
    await state.clear()

    tg_user = message.from_user
    if tg_user is None:
        return

    yandex = get_yandex_client()
    if not yandex.configured:
        await message.answer(
            "🤖 Разбор фото ещё не подключён. Скоро всё заработает!"
        )
        return

    if not ocr_available():
        await message.answer(
            "📸 Фото получил, но сейчас не могу распознать на нём текст.\n\n"
            "Можешь описать ситуацию словами — я разберусь."
        )
        return

    await message.answer("📸 Фото получил.\n\n🔎 Разбираюсь…")
    await message.bot.send_chat_action(message.chat.id, "typing")

    # Самая крупная версия фото
    photo = message.photo[-1] if message.photo else None
    if photo is None:
        await message.answer("Не удалось получить фото.")
        return

    tmp_path = None
    try:
        tmp_path = await download_telegram_file(
            bot=message.bot,
            file_id=photo.file_id,
            suffix=".jpg",
        )

        recognized = recognize_text(tmp_path)

        if not recognized:
            await message.answer(
                "🤔 По этому фото не удалось распознать текст.\n\n"
                "Попробуй:\n"
                "• прислать фото лучшего качества;\n"
                "• сделать снимок при хорошем освещении;\n"
                "• либо просто описать ситуацию словами."
            )
            return

        # Сохраняем как обычный текстовый запрос в БД
        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(
                session,
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                language=tg_user.language_code or "ru",
            )
            conv = await get_or_create_active_conversation(
                session,
                user_id=user.id,
                title="Фото",
                category="OTHER",
            )
            await save_user_message(
                session, conv.id, recognized, "photo"
            )

            system_prompt = build_system_prompt("OTHER") + "\n\n" + PHOTO_SYSTEM_ADDON
            user_message = build_user_message(
                user_text=recognized,
                memory=None,
                summary=None,
                history=None,
            )

            answer = await get_structured_answer(
                client=yandex,
                system_prompt=system_prompt,
                user_message=user_message,
            )
            formatted = format_answer(answer)

            await save_assistant_message(
                session,
                conversation_id=conv.id,
                content=formatted,
                model=answer.model or yandex.model_name,
                tokens=answer.tokens_total,
                message_type="photo",
            )

        await message.answer(formatted, reply_markup=after_answer_keyboard())
        await message.answer("Что дальше?", reply_markup=main_menu_after_answer())

    finally:
        safe_delete(tmp_path)