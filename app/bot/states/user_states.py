"""
FSM-состояния пользователя.

На этом этапе используем только одно — ожидание вопроса
после нажатия кнопки «🤖 Разобраться». Расширим позже.
"""

from aiogram.fsm.state import State, StatesGroup


class UserFlow(StatesGroup):
    waiting_for_question = State()