"""
История обращений.

На этом этапе — простая заглушка.
Полноценная реализация — на этапе 12.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="history")


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    await message.answer(
        "💬 <b>История</b>\n\n"
        "Пока история пуста. Как только вы начнёте разбирать ситуации, "
        "они появятся здесь."
    )


@router.message(F.text == "💬 История")
async def on_history_button(message: Message) -> None:
    await cmd_history(message)