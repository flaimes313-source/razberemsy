"""
Кнопки, которые показываются после ответа AI.

По ТЗ:
    🔍 Подробнее
    💬 Что ответить
    ➡️ Следующий шаг
    👍 Да   👎 Нет
"""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.bot.keyboards.main import (
    BTN_DOCUMENT,
    BTN_HELP,
    BTN_HISTORY,
    BTN_PHOTO,
    BTN_PRO,
    BTN_SOLVE,
)


BTN_DETAILS = "🔍 Подробнее"
BTN_REPLY = "💬 Что ответить"
BTN_NEXT = "➡️ Следующий шаг"


def after_answer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=BTN_DETAILS, callback_data="ai:details"),
                InlineKeyboardButton(text=BTN_REPLY, callback_data="ai:reply"),
            ],
            [
                InlineKeyboardButton(text=BTN_NEXT, callback_data="ai:next"),
            ],
            [
                InlineKeyboardButton(text="👍 Да", callback_data="fb:up"),
                InlineKeyboardButton(text="👎 Нет", callback_data="fb:down"),
            ],
        ]
    )


def main_menu_after_answer() -> ReplyKeyboardMarkup:
    """Меню, которое возвращаем пользователю после ответа."""
    keyboard = [
        [KeyboardButton(text=BTN_SOLVE)],
        [KeyboardButton(text=BTN_DOCUMENT), KeyboardButton(text=BTN_PHOTO)],
        [KeyboardButton(text=BTN_HISTORY), KeyboardButton(text=BTN_PRO)],
        [KeyboardButton(text=BTN_HELP)],
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Опишите ситуацию…",
    )