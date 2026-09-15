"""
Сервис анализа фото.

Приоритет:
    1. Yandex Vision OCR (работает везде, есть API-ключ).
    2. Tesseract (если установлен локально).
    3. Возврат None → бот честно сообщит, что не распознал.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.logging_config import get_logger
from app.services.vision_service import VisionError, get_vision_client

logger = get_logger(__name__)


def tesseract_available() -> bool:
    """Проверить, установлен ли бинарник tesseract."""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def recognize_with_tesseract(image_path: Path) -> Optional[str]:
    """Резервный путь — распознать текст через tesseract."""
    try:
        import pytesseract
        from PIL import Image

        with Image.open(image_path) as img:
            img = img.convert("L")
            text = pytesseract.image_to_string(img, lang="rus+eng")
        text = (text or "").strip()
        return text or None
    except Exception as exc:
        logger.warning("tesseract не сработал: %s", exc)
        return None


async def recognize_text_async(image_path: Path) -> Optional[str]:
    """
    Распознать текст на изображении.

    Сначала пробуем Yandex Vision, потом tesseract.
    Возвращает текст или None.
    """
    # 1. Yandex Vision
    vision = get_vision_client()
    if vision.configured:
        try:
            result = await vision.recognize(image_path, language="ru,en")
            if result and result.text:
                logger.info(
                    "Vision OCR: %s символов, язык=%s",
                    len(result.text),
                    result.language,
                )
                return result.text
        except VisionError as exc:
            logger.warning("Vision OCR не сработал: %s", exc)

    # 2. Tesseract (если установлен)
    if tesseract_available():
        logger.info("Пробуем tesseract как резерв")
        return recognize_with_tesseract(image_path)

    # 3. Нечем распознавать
    logger.info("Ни Vision, ни tesseract недоступны")
    return None