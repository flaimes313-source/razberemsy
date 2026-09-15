"""
Клиент YandexGPT.

Отправляет запрос к API Yandex Cloud Foundation Models.
Возвращает текст ответа + метрики (tokens, model).

Особенности:
- timeout из .env;
- 2–3 попытки при таймауте/сетевой ошибке;
- не логируем содержимое запроса/ответа (приватность).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)


class YandexGPTError(Exception):
    """Ошибка при обращении к YandexGPT."""


@dataclass
class CompletionResult:
    """Результат запроса к YandexGPT."""
    text: str
    model: str
    tokens_input: int = 0
    tokens_output: int = 0
    tokens_total: int = 0


class YandexGPT:
    """Асинхронный клиент YandexGPT."""

    def __init__(self) -> None:
        self._api_key = settings.yandex_api_key
        self._folder_id = settings.yandex_folder_id
        self._model = settings.yandex_model
        self._url = settings.yandex_api_url
        self._timeout = settings.yandex_timeout

    @property
    def configured(self) -> bool:
        return bool(self._api_key and self._folder_id)

    @property
    def model_name(self) -> str:
        return self._model

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Api-Key {self._api_key}",
            "Content-Type": "application/json",
        }

    def _payload(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float,
        max_tokens: int,
    ) -> dict[str, Any]:
        model_uri = f"gpt://{self._folder_id}/{self._model}/latest"
        return {
            "modelUri": model_uri,
            "completionOptions": {
                "stream": False,
                "temperature": temperature,
                "maxTokens": str(max_tokens),
            },
            "messages": [
                {"role": "system", "text": system_prompt},
                {"role": "user", "text": user_message},
            ],
        }

    async def complete(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        retries: int = 2,
    ) -> CompletionResult:
        """
        Отправить запрос и вернуть текст + метрики.

        При таймауте или 5xx — повторить запрос (до `retries` раз).
        """
        if not self.configured:
            raise YandexGPTError("YandexGPT не настроен (нет ключа или folder_id)")

        payload = self._payload(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        last_exc: Optional[Exception] = None

        for attempt in range(1, retries + 2):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.post(
                        self._url,
                        headers=self._headers(),
                        json=payload,
                    )

                if response.status_code >= 500:
                    raise YandexGPTError(f"YandexGPT 5xx: {response.status_code}")

                if response.status_code != 200:
                    snippet = response.text[:500]
                    if "does not match with service account folder" in snippet:
                        logger.error(
                            "YandexGPT 400: не совпадает folder_id и сервисный аккаунт. "
                            "Проверьте YANDEX_FOLDER_ID (должен начинаться с b1g…). "
                            "Ответ: %s",
                            snippet,
                        )
                    else:
                        logger.error(
                            "YandexGPT вернул %s: %s",
                            response.status_code,
                            snippet,
                        )
                    raise YandexGPTError(f"YandexGPT error {response.status_code}")

                data = response.json()
                return self._extract_result(data)

            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_exc = exc
                logger.warning(
                    "YandexGPT попытка %s/%s провалилась: %s",
                    attempt,
                    retries + 1,
                    type(exc).__name__,
                )
                if attempt <= retries:
                    await asyncio.sleep(1.5 * attempt)
                    continue
                raise YandexGPTError(f"YandexGPT недоступен: {exc}") from exc

        raise YandexGPTError(f"YandexGPT не ответил: {last_exc}")

    def _extract_result(self, data: dict[str, Any]) -> CompletionResult:
        """Достать текст и метрики из ответа YandexGPT."""
        try:
            result = data["result"]
            alternatives = result["alternatives"]
            message = alternatives[0]["message"]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise YandexGPTError("Некорректный ответ YandexGPT") from exc

        usage = result.get("usage") or {}
        tokens_input = int(usage.get("inputTextTokens", 0) or 0)
        tokens_output = int(usage.get("completionTokens", 0) or 0)
        tokens_total = int(
            usage.get("totalTokens", tokens_input + tokens_output) or 0
        )

        return CompletionResult(
            text=message.strip(),
            model=self._model,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            tokens_total=tokens_total,
        )


_yandex_client: Optional[YandexGPT] = None


def get_yandex_client() -> YandexGPT:
    global _yandex_client
    if _yandex_client is None:
        _yandex_client = YandexGPT()
    return _yandex_client