"""
Prompt Builder — сборка финального промпта для YandexGPT.

Складывает вместе:
    SYSTEM_PROMPT
    + категорийный промпт
    + требование JSON-формата
    + (опционально) память и summary
    + текущее сообщение пользователя
"""

from __future__ import annotations

from typing import Optional

from app.ai.prompts import (
    CATEGORY_PROMPTS,
    JSON_FORMAT_INSTRUCTION,
    SYSTEM_PROMPT,
)


def build_system_prompt(category: str) -> str:
    """Собрать системный промпт с учётом категории."""
    parts = [SYSTEM_PROMPT]

    category_prompt = CATEGORY_PROMPTS.get(category)
    if category_prompt:
        parts.append("\n\n" + category_prompt)

    parts.append("\n\n" + JSON_FORMAT_INSTRUCTION)
    return "".join(parts)


def build_user_message(
    user_text: str,
    memory: Optional[dict[str, str]] = None,
    summary: Optional[str] = None,
    history: Optional[list[dict[str, str]]] = None,
) -> str:
    """
    Собрать сообщение пользователя с контекстом.

    history — список словарей вида {"role": "user"/"assistant", "content": "..."}
    """
    parts: list[str] = []

    if memory:
        mem_lines = [f"- {k}: {v}" for k, v in memory.items()]
        parts.append("Известно о пользователе:\n" + "\n".join(mem_lines))

    if summary:
        parts.append("Краткое содержание предыдущего разговора:\n" + summary)

    if history:
        hist_lines = []
        for item in history:
            role = "Пользователь" if item.get("role") == "user" else "Помощник"
            hist_lines.append(f"{role}: {item.get('content', '')}")
        parts.append("Последние сообщения:\n" + "\n".join(hist_lines))

    parts.append("Текущая ситуация пользователя:\n" + user_text)
    return "\n\n".join(parts)