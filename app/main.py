"""
Точка входа приложения «Разберёмся».

Порядок:
    1. настройка логирования
    2. инициализация БД (создание таблиц, если их нет)
    3. создание Bot и Dispatcher
    4. регистрация команд
    5. запуск polling
    6. корректное закрытие при остановке
"""

from __future__ import annotations

import asyncio

from app.bot.bot import create_bot, create_dispatcher
from app.bot.commands import set_bot_commands
from app.database.database import close_db, init_db
from app.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


async def run() -> None:
    logger.info("Запуск проекта «Разберёмся»…")

    # 1. БД
    await init_db()

    # 2. Bot и Dispatcher
    bot = create_bot()
    dp = create_dispatcher()

    # 3. Команды
    await set_bot_commands(bot)

    # 4. Polling
    try:
        logger.info("Бот запущен, начинаю polling.")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await close_db()
        logger.info("Бот остановлен.")


def main() -> None:
    setup_logging()
    try:
        asyncio.run(run())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Остановка по запросу пользователя.")


if __name__ == "__main__":
    main()