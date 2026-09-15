"""
Валидатор ответа YandexGPT.

По ТЗ (этап 21):
    YandexGPT → JSON parse → ошибка? → повторный запрос
    → снова ошибка? → fallback

Пользователь НИКОГДА не должен увидеть JSONDecodeError.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from app.ai.yandexgpt import YandexGPT, YandexGPTError
from app.logging_config import get_logger

logger = get_logger(__name__)


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


@dataclass
class AIAnswer:
    summary: str = ""
    risks: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    dont_do: list[str] = field(default_factory=list)
    reply_text: Optional[str] = None
    followup_question: Optional[str] = None
    raw: str = ""
    tokens_total: int = 0
    model: str = ""


def _try_parse(raw: str) -> Optional[dict[str, Any]]:
    text = (raw or "").strip()
    if not text:
        return None

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


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    return []


def _to_answer(
    data: dict[str, Any],
    raw: str,
    tokens_total: int,
    model: str,
) -> AIAnswer:
    return AIAnswer(
        summary=str(data.get("summary") or "").strip(),
        risks=_normalize_list(data.get("risks")),
        actions=_normalize_list(data.get("actions")),
        dont_do=_normalize_list(data.get("dont_do")),
        reply_text=(str(data["reply_text"]).strip()
                    if data.get("reply_text") else None),
        followup_question=(str(data["followup_question"]).strip()
                           if data.get("followup_question") else None),
        raw=raw,
        tokens_total=tokens_total,
        model=model,
    )


async def get_structured_answer(
    client: YandexGPT,
    system_prompt: str,
    user_message: str,
) -> AIAnswer:
    """
    Запрос к YandexGPT + разбор JSON + 1 ретрай + fallback.

    Никогда не бросает наружу — всегда возвращает AIAnswer.
    """
    raw = ""
    tokens_total = 0
    model = client.model_name

    try:
        result = await client.complete(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=0.3,
            max_tokens=2000,
        )
        raw = result.text
        tokens_total = result.tokens_total
        model = result.model
    except YandexGPTError as exc:
        logger.error("YandexGPT недоступен: %s", exc)
        return AIAnswer(
            summary="Не получилось обработать запрос. "
                    "Попробуйте, пожалуйста, ещё раз.",
            model=model,
        )

    parsed = _try_parse(raw)
    if parsed:
        return _to_answer(parsed, raw, tokens_total, model)

    # 1 ретрай
    logger.warning("Некорректный JSON от YandexGPT, пробуем ретрай")
    retry_user = (
        user_message
        + "\n\nВАЖНО: верни ТОЛЬКО корректный JSON, "
        "без markdown-обёрток и пояснений."
    )
    try:
        result2 = await client.complete(
            system_prompt=system_prompt,
            user_message=retry_user,
            temperature=0.0,
            max_tokens=2000,
        )
        raw2 = result2.text
        tokens_total += result2.tokens_total
    except YandexGPTError as exc:
        logger.error("Повторный запрос тоже неудачен: %s", exc)
        return AIAnswer(
            summary="Не получилось обработать запрос. "
                    "Попробуйте, пожалуйста, ещё раз.",
            model=model,
        )

    parsed2 = _try_parse(raw2)
    if parsed2:
        return _to_answer(parsed2, raw2, tokens_total, model)

    logger.error("Fallback: не удалось получить JSON")
    return AIAnswer(
        summary=raw.strip() or "Не удалось разобрать ответ.",
        raw=raw,
        tokens_total=tokens_total,
        model=model,
    )