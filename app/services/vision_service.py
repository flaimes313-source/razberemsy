"""
Yandex Vision OCR — распознавание текста на изображениях.

Работает через тот же API-ключ, что и YandexGPT.
Не требует бинарника tesseract — работает на любом хостинге.

Документация API:
https://cloud.yandex.ru/docs/vision/ocr/api-ref/TextRecognition/recognize
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


OCR_URL = "https://ocr.api.cloud.yandex.net/ocr/v1/recognizeText"


@dataclass
class OCRResult:
    text: str
    language: str = ""
    model: str = ""


class VisionError(Exception):
    """Ошибка при обращении к Yandex Vision OCR."""


class VisionOCR:
    """Асинхронный клиент Yandex Vision OCR."""

    def __init__(self) -> None:
        self._api_key = settings.yandex_api_key
        self._folder_id = settings.yandex_folder_id
        self._timeout = settings.yandex_timeout

    @property
    def configured(self) -> bool:
        return bool(self._api_key and self._folder_id)

    async def recognize(
        self,
        image_path: Path,
        language: str = "ru",
        model: str = "page",
    ) -> Optional[OCRResult]:
        """
        Распознать текст на изображении.

        model:
            "page"          — для документов и скриншотов (по умолчанию);
            "page-column-sorting" — для многостолбцовых страниц;
            "handwritten"   — для рукописного текста.

        language:
            "ru", "en", "ru,en" и т.п.
        """
        if not self.configured:
            raise VisionError("Yandex Vision OCR не настроен")

        if not image_path.exists():
            raise VisionError(f"Файл не найден: {image_path}")

        # Читаем и кодируем в base64
        data = image_path.read_bytes()
        content = base64.b64encode(data).decode("ascii")

        payload = {
            "mimeType": _guess_mime(image_path),
            "languageCodes": [lang.strip() for lang in language.split(",")],
            "model": model,
            "content": content,
        }

        headers = {
            "Authorization": f"Api-Key {self._api_key}",
            "Content-Type": "application/json",
            "x-folder-id": self._folder_id,
        }

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(
                    OCR_URL,
                    headers=headers,
                    json=payload,
                )
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            raise VisionError(f"Vision OCR недоступен: {exc}") from exc

        if response.status_code != 200:
            snippet = response.text[:500]
            logger.error(
                "Vision OCR вернул %s: %s",
                response.status_code,
                snippet,
            )
            raise VisionError(f"Vision OCR error {response.status_code}")

        return self._parse_response(response.json())

    @staticmethod
    def _parse_response(data: dict) -> Optional[OCRResult]:
        try:
            result = data.get("result", {})
            text_annotation = result.get("textAnnotation", {})
            full_text = text_annotation.get("fullText", "")
            if not full_text:
                return None

            # Определим язык (Vision возвращает в properties)
            language = ""
            blocks = text_annotation.get("blocks") or []
            if blocks:
                langs = blocks[0].get("languages") or []
                if langs:
                    language = langs[0].get("languageCode", "")

            return OCRResult(
                text=full_text.strip(),
                language=language,
                model="vision-ocr",
            )
        except Exception as exc:
            logger.warning("Не удалось разобрать ответ Vision OCR: %s", exc)
            return None


def _guess_mime(path: Path) -> str:
    """Определить MIME по расширению."""
    suffix = path.suffix.lower()
    if suffix in (".jpg", ".jpeg"):
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".tiff":
        return "image/tiff"
    return "image/jpeg"


_vision_client: Optional[VisionOCR] = None


def get_vision_client() -> VisionOCR:
    global _vision_client
    if _vision_client is None:
        _vision_client = VisionOCR()
    return _vision_client