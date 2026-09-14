"""
Точка входа приложения «Разберёмся».

Схема (по ТЗ):
    main.py
      ↓
    загрузка config
      ↓
    подключение БД      (появится на этапе 2)
      ↓
    создание Bot
      ↓
    регистрация handlers
      ↓
    запуск
"""

from __future__ import annotations

import asyncio

from app.config import settings
from app.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


async def run() -> None:
    """Запуск приложения."""
    logger.info("Запуск проекта «Разберёмся»…")
    logger.info("Окружение: %s", settings.environment)

    # На следующих этапах здесь появится:
    #   1. инициализация БД
    #   2. создание Bot и Dispatcher
    #   3. регистрация handlers
    #   4. запуск polling
    #   5. запуск health-сервера FastAPI

    logger.info("Каркас проекта успешно инициализирован.")


def main() -> None:
    setup_logging()
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Остановка по запросу пользователя.")


if __name__ == "__main__":
    main()