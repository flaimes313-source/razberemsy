"""
Конфигурация проекта «Разберёмся».

Все настройки читаются из .env.
API-ключи и токены НЕ должны храниться в коде.
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

    # ===== Telegram =====
    telegram_bot_token: str = Field(..., alias="TELEGRAM_BOT_TOKEN")

    # ===== YandexGPT =====
    yandex_api_key: str = Field("", alias="YANDEX_API_KEY")
    yandex_folder_id: str = Field("", alias="YANDEX_FOLDER_ID")
    yandex_model: str = Field("yandexgpt-lite", alias="YANDEX_MODEL")
    yandex_api_url: str = Field(
        "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
        alias="YANDEX_API_URL",
    )
    yandex_timeout: int = Field(60, alias="YANDEX_TIMEOUT")

    # ===== База данных =====
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

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Синглтон настроек — читаем .env один раз за запуск."""
    return Settings()


settings = get_settings()