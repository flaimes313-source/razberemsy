"""
Обработчики кнопок:

- reply-кнопки: 📸 Фото, 📄 Документ (подсказки);
- inline-кнопки после ответа: ai:details, ai:reply, ai:next, fb:up, fb:down.

Логика inline-кнопок «Подробнее / Что ответить / Следующий шаг»
и полноценный feedback появятся на этапах 11 и 37–40.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards.main import BTN_DOCUMENT, BTN_PHOTO

router = Router(name="callbacks")


# ============================================================
# Reply-кнопки: 📸 Фото и 📄 Документ
# ============================================================
@router.message(F.text == BTN_PHOTO)
async def on_photo_button(message: Message) -> None:
    await message.answer(
        "📸 Просто отправьте фотографию или скриншот — я посмотрю "
        "и объясню, что видно и на что обратить внимание.\n\n"
        "<i>Можно отправлять без предварительного нажатия этой кнопки.</i>"
    )


@router.message(F.text == BTN_DOCUMENT)
async def on_document_button(message: Message) -> None:
    await message.answer(
        "📄 Отправьте документ (PDF, DOCX или TXT) — я разберу его "
        "и расскажу, на что обратить внимание.\n\n"
        "<i>Можно отправлять без предварительного нажатия этой кнопки.</i>"
    )


# ============================================================
# Inline-кнопки после ответа
# ============================================================
@router.callback_query(F.data == "ai:details")
async def on_details(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "🔍 <i>Подробный разбор появится в следующих обновлениях.</i>"
    )


@router.callback_query(F.data == "ai:reply")
async def on_reply(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "💬 <i>Готовые ответы появятся в следующих обновлениях.</i>"
    )


@router.callback_query(F.data == "ai:next")
async def on_next(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "➡️ <i>Функция «Следующий шаг» появится в следующих обновлениях.</i>"
    )


@router.callback_query(F.data == "fb:up")
async def on_feedback_up(callback: CallbackQuery) -> None:
    await callback.answer("Спасибо! 🙌", show_alert=False)


@router.callback_query(F.data == "fb:down")
async def on_feedback_down(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.answer(
        "Спасибо за сигнал. Скоро сможете указать, что было не так."
    )