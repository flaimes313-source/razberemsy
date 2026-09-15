"""
Обработчик документов.

Поддерживаемые форматы: PDF, DOCX, TXT.
Большие документы анализируются поэтапно (чанки → финальный анализ).
"""

from __future__ import annotations

from pathlib import Path

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.ai.formatter import format_answer
from app.ai.prompt_builder import build_system_prompt, build_user_message
from app.ai.validator import get_structured_answer
from app.ai.yandexgpt import get_yandex_client
from app.bot.keyboards.response import (
    after_answer_keyboard,
    main_menu_after_answer,
)
from app.database.database import AsyncSessionLocal
from app.database.repository import get_or_create_user
from app.services.document_service import (
    SUPPORTED_EXTENSIONS,
    extract_text,
    split_into_chunks,
)
from app.services.message_service import (
    get_or_create_active_conversation,
    save_assistant_message,
    save_user_message,
)
from app.utils.files import download_telegram_file, safe_delete
from app.logging_config import get_logger

router = Router(name="document")
logger = get_logger(__name__)


CHUNK_SYSTEM_ADDON = (
    "Ниже — фрагмент большого документа. "
    "Кратко выдели: тип информации, ключевые условия, платежи, сроки, "
    "штрафы, важные обязательства. Верни JSON по схеме: "
    '{"summary": "...", "risks": [...], "actions": [...], '
    '"dont_do": [], "reply_text": null, "followup_question": null}'
)


FINAL_SYSTEM_ADDON = (
    "Ниже — сводка по фрагментам большого документа. "
    "Собери общий итог: что это за документ, что важно, на что обратить "
    "внимание, что делать и чего не делать. Используй ту же JSON-схему."
)


@router.message(F.document)
async def on_document(message: Message, state: FSMContext) -> None:
    await state.clear()

    tg_user = message.from_user
    doc = message.document
    if tg_user is None or doc is None:
        return

    yandex = get_yandex_client()
    if not yandex.configured:
        await message.answer(
            "🤖 Разбор документов ещё не подключён. Скоро всё заработает!"
        )
        return

    file_name = doc.file_name or "document"
    suffix = Path(file_name).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        await message.answer(
            "Поддерживаются форматы: PDF, DOCX, TXT.\n"
            f"Ваш файл: <code>{file_name}</code>"
        )
        return

    await message.answer("📄 Документ получил.\n\n🔎 Проверяю содержание…")
    await message.bot.send_chat_action(message.chat.id, "typing")

    tmp_path = None
    try:
        tmp_path = await download_telegram_file(
            bot=message.bot,
            file_id=doc.file_id,
            suffix=suffix,
        )

        doc_text = extract_text(tmp_path)
        if doc_text is None or not doc_text.text.strip():
            await message.answer(
                "Не удалось извлечь текст из документа.\n\n"
                "Возможно, это скан без текстового слоя. "
                "Пришлите документ в текстовом виде (DOCX, TXT) "
                "или опишите ситуацию словами."
            )
            return

        if doc_text.truncated:
            await message.answer(
                "ℹ️ Документ большой — беру первые "
                f"{len(doc_text.text):,} символов для анализа."
            )

        chunks = split_into_chunks(doc_text.text)
        logger.info("Документ: %s, чанков: %s", file_name, len(chunks))

        # Сохраняем запрос пользователя (без самого текста документа)
        async with AsyncSessionLocal() as session:
            user = await get_or_create_user(
                session,
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                language=tg_user.language_code or "ru",
            )
            conv = await get_or_create_active_conversation(
                session,
                user_id=user.id,
                title=f"Документ: {file_name}"[:60],
                category="DOCUMENT",
            )
            # Сохраняем сам текст документа — по ТЗ (этап 59) его можно
            # не хранить, но тогда история будет неполной.
            # Храним до 20 000 символов, остальное опускаем.
            preview = doc_text.text[:20_000]
            await save_user_message(
                session, conv.id, preview, "document"
            )

            if len(chunks) == 1:
                # Небольшой документ — сразу в основной анализ
                system_prompt = build_system_prompt("DOCUMENT")
                user_message = build_user_message(
                    user_text=doc_text.text,
                    memory=None, summary=None, history=None,
                )
                answer = await get_structured_answer(
                    client=yandex,
                    system_prompt=system_prompt,
                    user_message=user_message,
                )
            else:
                # Большой документ — поэтапно
                summaries: list[str] = []
                total_tokens = 0
                for idx, chunk in enumerate(chunks, start=1):
                    logger.info("Анализ чанка %s/%s", idx, len(chunks))
                    partial = await get_structured_answer(
                        client=yandex,
                        system_prompt=build_system_prompt("DOCUMENT")
                        + "\n\n" + CHUNK_SYSTEM_ADDON,
                        user_message=f"Фрагмент {idx} из {len(chunks)}:\n\n{chunk}",
                    )
                    total_tokens += partial.tokens_total
                    if partial.summary:
                        summaries.append(f"[{idx}/{len(chunks)}] {partial.summary}")

                # Финальный анализ
                combined = "\n".join(summaries)
                answer = await get_structured_answer(
                    client=yandex,
                    system_prompt=build_system_prompt("DOCUMENT")
                    + "\n\n" + FINAL_SYSTEM_ADDON,
                    user_message=combined,
                )
                answer.tokens_total += total_tokens

            formatted = format_answer(answer)
            await save_assistant_message(
                session,
                conversation_id=conv.id,
                content=formatted,
                model=answer.model or yandex.model_name,
                tokens=answer.tokens_total,
                message_type="document",
            )

        await message.answer(formatted, reply_markup=after_answer_keyboard())
        await message.answer("Что дальше?", reply_markup=main_menu_after_answer())

    finally:
        safe_delete(tmp_path)