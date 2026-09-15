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
    """
    Создать Dispatcher и зарегистрировать все роутеры.

    Порядок регистрации КРИТИЧЕН:
        1) команды /start, /help, /history, /pro;
        2) reply-кнопки и inline-кнопки (callbacks);
        3) фото и документы — ДО обычного текста;
        4) обычный текст (message) — ПОСЛЕДНИМ.
    """
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(handlers_pkg.start.router)
    dp.include_router(handlers_pkg.help.router)
    dp.include_router(handlers_pkg.history.router)
    dp.include_router(handlers_pkg.subscription.router)
    dp.include_router(handlers_pkg.callbacks.router)

    # Фото и документы подключаем ДО message.
    # Если подключить после — message.router с F.text их не поймает,
    # но правило «специфичные фильтры раньше общих» соблюдаем всегда.
    dp.include_router(handlers_pkg.photo.router)
    dp.include_router(handlers_pkg.document.router)

    # Обычный текст — ПОСЛЕДНИМ.
    dp.include_router(handlers_pkg.message.router)

    return dp