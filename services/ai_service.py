from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)


class AIServiceError(RuntimeError):
    pass


class EmptyAIResponseError(AIServiceError):
    pass


class AIService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "Telegram Auto Post Bot",
        }
        return headers

    def _client_kwargs(self) -> dict[str, object]:
        kwargs: dict[str, object] = {
            "timeout": self.settings.request_timeout,
        }

        proxies = self.settings.proxies()
        if proxies:
            kwargs["proxy"] = proxies.get("https://") or proxies.get("http://")

        return kwargs

    async def chat(self, prompt: str, system: str | None = None, temperature: float = 0.7) -> str:
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.settings.openrouter_model,
            "messages": messages,
            "temperature": temperature,
        }

        last_error: Exception | None = None
        for attempt in range(1, self.settings.request_retries + 1):
            try:
                async with httpx.AsyncClient(**self._client_kwargs()) as client:
                    response = await client.post(
                        f"{self.settings.openrouter_base_url.rstrip('/')}/chat/completions",
                        headers=self._headers(),
                        json=payload,
                    )
                if response.status_code != 200:
                    logger.error(
                        "OpenRouter error %s: %s",
                        response.status_code,
                        response.text)
                    response.raise_for_status()
                data = response.json()
                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                if not content or not content.strip():
                    raise EmptyAIResponseError("OpenRouter returned an empty response")
                return content.strip()

            except (httpx.TimeoutException, httpx.HTTPError, EmptyAIResponseError) as exc:
                last_error = exc
                logger.exception("OpenRouter attempt %s failed", attempt)
                if attempt < self.settings.request_retries:
                    await asyncio.sleep(1.5 * attempt)

        raise AIServiceError("Не удалось получить ответ от AI") from last_error
