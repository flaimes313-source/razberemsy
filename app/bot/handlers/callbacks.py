"""
Обработчик кнопок «📄 Документ», «📸 Фото» и других сообщений,
которые пока не реализованы.

В этапах 9–10 здесь появится реальная логика.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from app.bot.keyboards.main import BTN_DOCUMENT, BTN_PHOTO

router = Router(name="callbacks")


@router.message(F.text == BTN_PHOTO)
async def on_photo_button(message: Message) -> None:
    await message.answer(
        "📸 Отправьте фотографию или скриншот — я посмотрю и объясню, "
        "что видно и на что обратить внимание.\n\n"
        "<i>Анализ фото появится в следующих обновлениях.</i>"
    )


@router.message(F.text == BTN_DOCUMENT)
async def on_document_button(message: Message) -> None:
    await message.answer(
        "📄 Отправьте документ (PDF, DOCX или TXT) — я разберу его "
        "и расскажу, на что обратить внимание.\n\n"
        "<i>Разбор документов появится в следующих обновлениях.</i>"
    )