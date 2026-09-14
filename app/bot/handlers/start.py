"""
Обработчик команды /start и нажатия кнопки «🤖 Разобраться».

По ТЗ текст приветствия:
    👋 Привет! Я — Разберёмся.
    ...
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from app.bot.keyboards.main import BTN_SOLVE, main_menu
from app.bot.states.user_states import UserFlow
from app.database.database import AsyncSessionLocal
from app.database.repository import get_or_create_user
from app.logging_config import get_logger

router = Router(name="start")
logger = get_logger(__name__)


WELCOME_TEXT = (
    "👋 Привет! Я — <b>Разберёмся</b>.\n\n"
    "Не знаешь, что делать в какой-то ситуации?\n\n"
    "Просто расскажи мне, что произошло.\n\n"
    "Я помогу:\n"
    "• понять ситуацию;\n"
    "• найти возможные риски;\n"
    "• разобраться с документом;\n"
    "• оценить покупку или предложение;\n"
    "• составить ответ;\n"
    "• определить, что делать дальше.\n\n"
    "Можно отправить текст, фото, скриншот или документ.\n\n"
    "👇 Просто расскажи, что случилось."
)


async def _register_user(message: Message) -> None:
    """Найти или создать пользователя в БД."""
    tg_user = message.from_user
    if tg_user is None:
        return
    async with AsyncSessionLocal() as session:
        await get_or_create_user(
            session,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            language=tg_user.language_code or "ru",
        )


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _register_user(message)
    await message.answer(WELCOME_TEXT, reply_markup=main_menu())


@router.message(F.text == BTN_SOLVE)
async def on_solve_button(message: Message, state: FSMContext) -> None:
    await _register_user(message)
    await state.set_state(UserFlow.waiting_for_question)
    await message.answer(
        "Опишите, что случилось. Можно одним сообщением — "
        "я разберусь и подскажу, что делать дальше."
    )