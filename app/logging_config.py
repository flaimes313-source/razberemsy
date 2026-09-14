"""
Настройка логирования для проекта «Разберёмся».

Правила:
- единый формат логов;
- уровень берётся из .env;
- логи не должны содержать содержимое приватных сообщений и документов.
"""

from __future__ import annotations

import logging
import sys
from typing import Final

from app.config import settings

LOG_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """Инициализация корневого логгера. Вызывается один раз при запуске."""
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    # Убираем возможные дубли при повторной инициализации
    for handler in list(root.handlers):
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT))
    root.addHandler(handler)

    # Приглушаем слишком болтливые библиотеки
    logging.getLogger("aiogram").setLevel(logging.INFO)
    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Удобный хелпер для получения логгера по имени модуля."""
    return logging.getLogger(name)