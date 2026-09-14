"""
Создание Bot и Dispatcher, регистрация handlers.

Здесь же — middleware, если понадобится.
"""

from __future__ import annotations

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from app.config import settings
from app.logging_config import get_logger
from app.bot import handlers as handlers_pkg


logger = get_logger(__name__)


def create_bot() -> Bot:
    """Создать объект Bot с дефолтными настройками."""
    return Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    """Создать Dispatcher и зарегистрировать все роутеры."""
    dp = Dispatcher(storage=MemoryStorage())

    # Порядок регистрации важен:
    #   1) команды /start, /help и т.д.
    #   2) обработчики кнопок
    #   3) fallback — обычный текст
    dp.include_router(handlers_pkg.start.router)
    dp.include_router(handlers_pkg.help.router)
    dp.include_router(handlers_pkg.history.router)
    dp.include_router(handlers_pkg.subscription.router)
    dp.include_router(handlers_pkg.callbacks.router)
    dp.include_router(handlers_pkg.message.router)
    # photo / document пока не подключаем — добавим в этапах 9–10

    return dp