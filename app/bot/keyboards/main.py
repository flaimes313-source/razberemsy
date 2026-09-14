"""
Главное меню бота.

По ТЗ:
    🤖 Разобраться
    📄 Документ
    📸 Фото

    💬 История
    ⭐ PRO
    ℹ️ Как это работает
"""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


BTN_SOLVE = "🤖 Разобраться"
BTN_DOCUMENT = "📄 Документ"
BTN_PHOTO = "📸 Фото"
BTN_HISTORY = "💬 История"
BTN_PRO = "⭐ PRO"
BTN_HELP = "ℹ️ Как это работает"


def main_menu() -> ReplyKeyboardMarkup:
    """Основное меню пользователя."""
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