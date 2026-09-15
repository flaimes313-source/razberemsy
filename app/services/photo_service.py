"""
Сервис анализа фото.

Сценарий:
    1. Скачиваем фото.
    2. OCR — распознаём текст с картинки (если доступно).
    3. Возвращаем распознанный текст.

Если OCR недоступен — сообщаем об этом вызывающему коду.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.logging_config import get_logger

logger = get_logger(__name__)


def ocr_available() -> bool:
    """Проверить, установлен ли tesseract."""
    try:
        import pytesseract  # noqa: F401
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def recognize_text(image_path: Path) -> Optional[str]:
    """
    Распознать текст на изображении.

    Возвращает строку или None, если не удалось.
    """
    try:
        import pytesseract
        from PIL import Image

        with Image.open(image_path) as img:
            # Предобработка: ч/б, повышение контраста даёт
            # заметно лучший OCR на скриншотах.
            img = img.convert("L")
            text = pytesseract.image_to_string(img, lang="rus+eng")
        text = (text or "").strip()
        return text or None
    except Exception as exc:
        logger.warning("OCR не сработал: %s", exc)
        return None