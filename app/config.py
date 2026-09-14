"""
Конфигурация проекта «Разберёмся».

Все настройки читаются из .env.
API-ключи и токены НЕ должны храниться в коде.

Особенности:
- TELEGRAM_BOT_TOKEN и DATABASE_URL обязательны всегда;
- YANDEX_API_KEY / YANDEX_FOLDER_ID можно оставить пустыми
  на этапе, пока YandexGPT ещё не подключён;
- ADMIN_IDS парсится из строки "111,222" или "111 222";
- DATABASE_URL автоматически приводится к async-драйверу asyncpg.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Главный объект настроек приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== Telegram (обязательно) =====
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")

    # ===== YandexGPT (необязательно на этапе 2-3) =====
    yandex_api_key: str = Field("", alias="YANDEX_API_KEY")
    yandex_folder_id: str = Field("", alias="YANDEX_FOLDER_ID")
    yandex_model: str = Field("yandexgpt-lite", alias="YANDEX_MODEL")
    yandex_api_url: str = Field(
        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        alias="YANDEX_API_URL",
    )
    yandex_timeout: int = Field(60, alias="YANDEX_TIMEOUT")

    # ===== База данных (обязательно) =====
    database_url: str = Field(..., alias="DATABASE_URL")

    # ===== Администраторы =====
    admin_ids: List[int] = Field(default_factory=list, alias="ADMIN_IDS")

    # ===== Лимиты FREE =====
    free_daily_limit: int = Field(5, alias="FREE_DAILY_LIMIT")
    free_photo_limit: int = Field(2, alias="FREE_PHOTO_LIMIT")
    free_document_limit: int = Field(1, alias="FREE_DOCUMENT_LIMIT")

    # ===== Лимиты PRO =====
    pro_monthly_limit: int = Field(150, alias="PRO_MONTHLY_LIMIT")
    pro_photo_limit: int = Field(30, alias="PRO_PHOTO_LIMIT")
    pro_document_limit: int = Field(10, alias="PRO_DOCUMENT_LIMIT")

    # ===== Лимиты PRO+ =====
    pro_plus_monthly_limit: int = Field(400, alias="PRO_PLUS_MONTHLY_LIMIT")
    pro_plus_photo_limit: int = Field(100, alias="PRO_PLUS_PHOTO_LIMIT")
    pro_plus_document_limit: int = Field(30, alias="PRO_PLUS_DOCUMENT_LIMIT")

    # ===== Приложение =====
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    environment: str = Field("development", alias="ENVIRONMENT")

    # ========================================================
    #  Валидаторы
    # ========================================================
    @field_validator("admin_ids", mode="before")
    @classmethod
    def parse_admin_ids(cls, value):
        """Преобразует строку '111,222' или '111 222' в список int."""
        if value is None or value == "":
            return []
        if isinstance(value, list):
            return [int(v) for v in value]
        if isinstance(value, str):
            cleaned = value.replace(",", " ").strip()
            return [int(part) for part in cleaned.split() if part.strip()]
        if isinstance(value, int):
            return [value]
        return value

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value):
        """
        Приводит строку подключения к async-драйверу asyncpg.

        BotHost часто даёт URL без указания драйвера:
            postgresql://...
            postgres://...
        SQLAlchemy тогда берёт psycopg2 (sync), которого нет.

        Автоматически заменяем префикс на postgresql+asyncpg://.
        """
        if not isinstance(value, str):
            return value
        url = value.strip()
        if url.startswith("postgres://"):
            return "postgresql+asyncpg://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + url[len("postgresql://"):]
        return url

    # ========================================================
    #  Свойства
    # ========================================================
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def yandex_configured(self) -> bool:
        """YandexGPT настроен? Нужно ли использовать AI."""
        return bool(self.yandex_api_key and self.yandex_folder_id)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Синглтон настроек.

    Если чего-то не хватает — выдаём понятное сообщение
    вместо длинного traceback от pydantic.
    """
    try:
        return Settings()
    except Exception as exc:
        import os

        missing = []
        for name in ("TELEGRAM_BOT_TOKEN", "DATABASE_URL"):
            if not os.environ.get(name):
                missing.append(name)

        hint = (
            "\n\nПроверьте переменные окружения на BotHost.\n"
            "Обязательно должны быть заданы:\n"
            "  TELEGRAM_BOT_TOKEN\n"
            "  DATABASE_URL\n\n"
            "Необязательные, но нужные позже (для YandexGPT):\n"
            "  YANDEX_API_KEY\n"
            "  YANDEX_FOLDER_ID\n"
        )
        if missing:
            hint = (
                f"\n\nНе заданы обязательные переменные: {', '.join(missing)}"
                + hint
            )
        raise RuntimeError(f"Ошибка конфигурации: {exc}{hint}") from exc


settings = get_settings()