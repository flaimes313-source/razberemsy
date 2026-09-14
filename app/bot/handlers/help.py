"""
Обработчик /help и кнопки «ℹ️ Как это работает».
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")


HELP_TEXT = (
    "ℹ️ <b>Как это работает</b>\n\n"
    "1. Вы описываете ситуацию обычными словами.\n"
    "2. Я определяю, что это за ситуация.\n"
    "3. Готовлю понятный ответ: что происходит и что делать дальше.\n\n"
    "Что можно отправлять:\n"
    "• текст;\n"
    "• фото или скриншот;\n"
    "• документ (PDF, DOCX, TXT).\n\n"
    "Дополнительно:\n"
    "• 💬 Что ответить — готовый текст ответа;\n"
    "• 🔍 Подробнее — раскрыть ситуацию;\n"
    "• ➡️ Следующий шаг — что делать первым делом.\n\n"
    "Команды:\n"
    "/start — начать\n"
    "/help — эта справка\n"
    "/history — история обращений\n"
    "/pro — тарифы"
)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT)


@router.message(F.text == "ℹ️ Как это работает")
async def on_help_button(message: Message) -> None:
    await message.answer(HELP_TEXT)