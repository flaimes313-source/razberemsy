"""
Сервис работы с документами.

Поддерживает PDF, DOCX, TXT.
Большие документы режет на чанки и анализирует поэтапно.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.logging_config import get_logger

logger = get_logger(__name__)


SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt"}

# Размер чанка в символах (примерно 4000 знаков — оптимально для AI)
CHUNK_SIZE = 4000
# Максимальный размер документа для обработки (в символах)
MAX_TEXT_LENGTH = 120_000


@dataclass
class DocumentText:
    """Извлечённый текст документа."""
    text: str
    pages: int = 0
    truncated: bool = False


def extract_text(path: Path) -> Optional[DocumentText]:
    """Извлечь текст из PDF/DOCX/TXT. Возвращает None, если не удалось."""
    suffix = path.suffix.lower()
    try:
        if suffix == ".pdf":
            return _extract_pdf(path)
        if suffix == ".docx":
            return _extract_docx(path)
        if suffix == ".txt":
            return _extract_txt(path)
    except Exception as exc:
        logger.warning("Не удалось извлечь текст из %s: %s", path.name, exc)
    return None


def _extract_pdf(path: Path) -> DocumentText:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = len(reader.pages)
    parts: list[str] = []
    for page in reader.pages:
        try:
            parts.append(page.extract_text() or "")
        except Exception:
            parts.append("")
    text = "\n".join(parts).strip()
    return _truncate(text, pages=pages)


def _extract_docx(path: Path) -> DocumentText:
    from docx import Document

    doc = Document(str(path))
    parts = [p.text for p in doc.paragraphs if p.text]
    text = "\n".join(parts).strip()
    return _truncate(text, pages=0)


def _extract_txt(path: Path) -> DocumentText:
    # Пробуем utf-8, при неудаче — cp1251
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="cp1251", errors="replace")
    return _truncate(text, pages=0)


def _truncate(text: str, pages: int) -> DocumentText:
    truncated = False
    if len(text) > MAX_TEXT_LENGTH:
        text = text[:MAX_TEXT_LENGTH]
        truncated = True
    return DocumentText(text=text, pages=pages, truncated=truncated)


def split_into_chunks(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Разбить текст на чанки, стараясь не рвать абзацы."""
    if not text:
        return []

    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for p in paragraphs:
        if current_len + len(p) > chunk_size and current:
            chunks.append("\n".join(current))
            current = [p]
            current_len = len(p)
        else:
            current.append(p)
            current_len += len(p) + 1

    if current:
        chunks.append("\n".join(current))

    return chunks