"""
Тарифы PRO / PRO+.

На этом этапе — информационная заглушка.
Активация подписки появится на этапе 14.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="subscription")


PRO_TEXT = (
    "⭐ <b>Тарифы</b>\n\n"
    "<b>Бесплатно</b>\n"
    "• 5 обращений в день\n"
    "• 2 фото в день\n"
    "• 1 документ в день\n\n"
    "<b>PRO — 299 ₽ / месяц</b>\n"
    "• 150 AI-запросов в месяц\n"
    "• 30 фото\n"
    "• 10 документов\n"
    "• история и память\n\n"
    "<b>PRO+ — 499 ₽ / месяц</b>\n"
    "• 400 AI-запросов\n"
    "• 100 фото\n"
    "• 30 документов\n"
    "• расширенный анализ\n"
    "• приоритетная обработка\n\n"
    "Оплата будет доступна в ближайшее время."
)


@router.message(Command("pro"))
async def cmd_pro(message: Message) -> None:
    await message.answer(PRO_TEXT)


@router.message(F.text == "⭐ PRO")
async def on_pro_button(message: Message) -> None:
    await cmd_pro(message)