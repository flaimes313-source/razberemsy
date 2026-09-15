"""
Работа с файлами: временные пути, безопасное удаление, скачивание.
"""

from __future__ import annotations

import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional

from aiogram import Bot
from aiogram.types import File

from app.logging_config import get_logger

logger = get_logger(__name__)


TEMP_DIR = Path(tempfile.gettempdir()) / "razberemsya"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def make_temp_path(suffix: str = "") -> Path:
    """Уникальный путь во временной папке."""
    name = f"{uuid.uuid4().hex}{suffix}"
    return TEMP_DIR / name


def safe_delete(path: Optional[Path]) -> None:
    """Удалить файл, если существует. Не бросает исключений."""
    if path is None:
        return
    try:
        if path.exists():
            path.unlink()
    except OSError as exc:
        logger.warning("Не удалось удалить временный файл %s: %s", path, exc)


async def download_telegram_file(
    bot: Bot,
    file_id: str,
    suffix: str = "",
) -> Path:
    """
    Скачать файл из Telegram во временную папку.

    Возвращает путь к скачанному файлу.
    """
    tg_file: File = await bot.get_file(file_id)
    dest = make_temp_path(suffix=suffix)

    await bot.download_file(tg_file.file_path, destination=dest)
    logger.info("Файл скачан: %s (%s байт)", dest.name, dest.stat().st_size)
    return dest