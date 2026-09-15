"""
Formatter — превращает AIAnswer в красивое сообщение для Telegram.

По ТЗ (этап 19) используем блоки:
    🔎 Что происходит
    ⚠️ На что обратить внимание
    ✅ Что делать
    ❌ Чего не делать
    💬 Что можно ответить
    ➡️ (followup_question)

Показываем ТОЛЬКО те блоки, которые заполнены.
"""

from __future__ import annotations

from app.ai.validator import AIAnswer


def _render_list(items: list[str]) -> str:
    return "\n".join(f"• {item}" for item in items)


def format_answer(answer: AIAnswer) -> str:
    blocks: list[str] = []

    if answer.summary:
        blocks.append("🔎 <b>Что происходит</b>\n" + answer.summary)

    if answer.risks:
        blocks.append(
            "⚠️ <b>На что обратить внимание</b>\n" + _render_list(answer.risks)
        )

    if answer.actions:
        blocks.append("✅ <b>Что делать</b>\n" + _render_list(answer.actions))

    if answer.dont_do:
        blocks.append(
            "❌ <b>Чего не делать</b>\n" + _render_list(answer.dont_do)
        )

    if answer.reply_text:
        blocks.append(
            "💬 <b>Что можно ответить</b>\n" + f"<i>{answer.reply_text}</i>"
        )

    if answer.followup_question:
        blocks.append(
            "❓ <b>Уточнение</b>\n" + answer.followup_question
        )

    if not blocks:
        return "Не удалось собрать ответ. Попробуйте, пожалуйста, ещё раз."

    return "\n\n".join(blocks)