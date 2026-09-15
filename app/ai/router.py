"""
AI Router — определяет категорию ситуации.

По ТЗ (этап 17) — не гоняем каждое сообщение через AI.
Сначала пробуем локальные эвристики (быстро и бесплатно).
Если неоднозначно — обращаемся к YandexGPT.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

from app.ai.yandexgpt import YandexGPT, YandexGPTError
from app.logging_config import get_logger

logger = get_logger(__name__)


CATEGORIES = (
    "DOCUMENT",
    "SCAM",
    "MONEY",
    "PURCHASE",
    "HOME",
    "CAR",
    "WORK",
    "FAMILY",
    "TRAVEL",
    "TECH",
    "HEALTH",
    "LEGAL",
    "OTHER",
)


@dataclass
class RouteResult:
    category: str
    confidence: float
    requires_clarification: bool = False
    source: str = "local"  # "local" или "ai"


# ============================================================
# Локальные ключевые слова
# ============================================================
_LOCAL_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("SCAM", (
        "мошенник", "мошенничеств", "обман", "фишинг", "взлом",
        "банк", "звонок из банка", "служба безопасности",
        "пришло сообщение", "подозрительн", "код из смс",
        "перевести деньги", "незнакомый номер", "списали",
    )),
    ("DOCUMENT", (
        "договор", "документ", "проверь документ", "прочитай",
        "оферта", "соглашение", "приложение к договору",
        "пункт", "условия", "расторжен", "акт",
    )),
    ("PURCHASE", (
        "купить", "покупк", "товар", "магазин", "вернул",
        "возврат", "продавец", "маркетплейс", "озон", "wildberries",
        "брак", "гаранти", "чек", "сравн",
    )),
    ("CAR", (
        "машин", "авто", "автомобил", "двигател", "check engine",
        "шина", "колес", "коробка", "коробка передач", "kиа", "kia",
        "тойота", "toyota", "бмв", "bmw", "рено", "renault", "лада",
    )),
    ("HOME", (
        "стиральн", "холодильник", "пылесос", "посудомоечн",
        "микроволнов", "кондиционер", "кран", "трубы", "проводк",
        "розетк", "выключател", "не работает",
    )),
    ("WORK", (
        "начальник", "работодател", "увольн", "зарплат", "отпуск",
        "объяснительн", "коллег", "работа", "трудовой договор",
        "заявление", "премия", "выговор", "собеседован",
    )),
    ("MONEY", (
        "кредит", "ипотек", "процент", "вклад", "инвестиц",
        "взнос", "платеж", "рассрочк", "долг", "переплат",
    )),
    ("FAMILY", (
        "жена", "муж", "ребен", "ребён", "семья", "развод",
        "алимент", "родител", "свекров", "тёщ", "тещ",
    )),
    ("TRAVEL", (
        "поездк", "путёвк", "путевк", "виз", "отел", "отель",
        "билет", "рейс", "самолёт", "самолет", "тур",
    )),
    ("TECH", (
        "телефон", "компьютер", "ноутбук", "windows", "андроид",
        "android", "iphone", "приложени", "роутер",
        "wi-fi", "wifi", "интернет", "сайт", "программ",
    )),
    ("HEALTH", (
        "болит", "температур", "врач", "анализ", "таблетк",
        "лекарств", "симптом", "диагноз", "больничн",
    )),
    ("LEGAL", (
        "юрист", "суд", "иск", "закон", "стать", "штраф",
        "гибдд", "пристав", "нотариус", "жалоб", "прокуратур",
    )),
]


def _local_route(text: str) -> Optional[RouteResult]:
    """Быстрая попытка определить категорию по ключевым словам."""
    low = text.lower()

    best_category: Optional[str] = None
    best_count = 0

    for category, keywords in _LOCAL_RULES:
        count = sum(1 for kw in keywords if kw in low)
        if count > best_count:
            best_count = count
            best_category = category

    if best_category is None:
        return None

    # Если найдено 1 ключевое слово — уверенность средняя
    # Если 2+ — уверенность высокая
    confidence = 0.75 if best_count == 1 else 0.9
    return RouteResult(
        category=best_category,
        confidence=confidence,
        source="local",
    )


# ============================================================
# AI-роутинг
# ============================================================
_ROUTER_SYSTEM = (
    "Ты — классификатор бытовых ситуаций. "
    "Определи категорию обращения пользователя. "
    "Верни ТОЛЬКО JSON без пояснений:\n"
    '{"category": "SCAM", "confidence": 0.94}\n\n'
    "Категории: DOCUMENT, SCAM, MONEY, PURCHASE, HOME, CAR, WORK, "
    "FAMILY, TRAVEL, TECH, HEALTH, LEGAL, OTHER."
)


async def _ai_route(text: str, client: YandexGPT) -> Optional[RouteResult]:
    """Резервный путь: спросить категорию у AI."""
    if not client.configured:
        return None
    try:
        result = await client.complete(
            system_prompt=_ROUTER_SYSTEM,
            user_message=text,
            temperature=0.0,
            max_tokens=100,
        )
    except YandexGPTError as exc:
        logger.warning("AI router недоступен: %s", exc)
        return None

    data = _safe_parse_json(result.text)
    if not data:
        return None

    category = str(data.get("category", "OTHER")).upper()
    if category not in CATEGORIES:
        category = "OTHER"

    try:
        confidence = float(data.get("confidence", 0.5))
    except (TypeError, ValueError):
        confidence = 0.5

    return RouteResult(
        category=category,
        confidence=confidence,
        source="ai",
    )


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _safe_parse_json(text: str) -> Optional[dict]:
    """Попытка вытащить JSON из ответа (на случай обёрток)."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = _JSON_RE.search(text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
    return None


# ============================================================
# Публичная функция
# ============================================================
async def route_message(
    text: str,
    client: Optional[YandexGPT] = None,
) -> RouteResult:
    """
    Определить категорию сообщения.

    Сначала локальные эвристики, потом (при неудаче) — AI.
    """
    local = _local_route(text)
    if local and local.confidence >= 0.75:
        logger.info("Router: %s (local)", local.category)
        return local

    # Если клиент не передан — вернуть локальный результат или OTHER
    if client is None:
        if local:
            return local
        return RouteResult(category="OTHER", confidence=0.3, source="local")

    ai = await _ai_route(text, client)
    if ai:
        logger.info("Router: %s (ai, conf=%.2f)", ai.category, ai.confidence)
        return ai

    if local:
        return local
    return RouteResult(category="OTHER", confidence=0.3, source="local")