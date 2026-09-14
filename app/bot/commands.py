"""
Регистрация команд Telegram-бота при запуске.

Дополнительно: список команд для меню «/» в Telegram.
"""

from __future__ import annotations

from aiogram import Bot
from aiogram.types import BotCommand

from app.logging_config import get_logger

logger = get_logger(__name__)


COMMANDS = [
    BotCommand(command="start", description="Начать работу"),
    BotCommand(command="help", description="Как это работает"),
    BotCommand(command="history", description="История обращений"),
    BotCommand(command="pro", description="Тарифы PRO"),
]


async def set_bot_commands(bot: Bot) -> None:
    """Установить команды бота в Telegram."""
    try:
        await bot.set_my_commands(COMMANDS)
        logger.info("Команды бота зарегистрированы.")
    except Exception as exc:
        logger.warning("Не удалось зарегистрировать команды: %s", exc)