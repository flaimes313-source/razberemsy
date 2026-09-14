# Разберёмся

Telegram-бот «Разберёмся» — интеллектуальный бытовой помощник на базе YandexGPT.

Пользователь просто описывает ситуацию, а бот:
- определяет категорию;
- формирует понятный ответ;
- предлагает следующие шаги;
- помогает составить ответ;
- умеет работать с фото и документами.

## Стек

- Python 3.12+
- aiogram 3.x
- FastAPI
- SQLAlchemy 2.x
- PostgreSQL (BotHost)
- YandexGPT
- httpx / pydantic / pydantic-settings

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt