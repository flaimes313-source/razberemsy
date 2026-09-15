"""
Пакет handlers.

Регистрируем все модули-обработчики.
Порядок импорта неважен — важен порядок включения роутеров в bot.py.
"""

from app.bot.handlers import (  # noqa: F401
    callbacks,
    document,
    help,
    history,
    message,
    photo,
    start,
    subscription,
)

__all__ = [
    "callbacks",
    "document",
    "help",
    "history",
    "message",
    "photo",
    "start",
    "subscription",
]