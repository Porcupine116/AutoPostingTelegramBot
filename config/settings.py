from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(..., alias="BOT_TOKEN")
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field("google/gemini-2.0-flash-001", alias="OPENROUTER_MODEL")
    openrouter_base_url: str = Field("https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL")

    http_proxy: str | None = Field(default=None, alias="HTTP_PROXY")
    https_proxy: str | None = Field(default=None, alias="HTTPS_PROXY")

    default_style: str = Field("простым и человеческим", alias="DEFAULT_STYLE")
    default_format: str = Field("короткий пост", alias="DEFAULT_FORMAT")
    default_language: str = Field("ru", alias="DEFAULT_LANGUAGE")

    database_path: Path = Field(default=Path("./data/history.sqlite3"), alias="DATABASE_PATH")
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    request_timeout: float = Field(60.0, alias="REQUEST_TIMEOUT")
    request_retries: int = Field(3, alias="REQUEST_RETRIES")
    max_message_length: int = Field(3800, alias="MAX_MESSAGE_LENGTH")

    # Автопостинг
    admin_chat_id: int | None = Field(default=None, alias="ADMIN_CHAT_ID")
    channel_id: str | None = Field(default=None, alias="CHANNEL_ID")
    schedule_timezone: str = Field("Europe/Vilnius", alias="SCHEDULE_TIMEZONE")
    autopost_mode: str = Field("approve", alias="AUTOPOST_MODE")  # approve | auto

    content_topic: str = Field(
        "ДТП, страховые выплаты, автоюрист и судебная практика",
        alias="CONTENT_TOPIC",
    )
    content_style: str = Field("простым и человеческим", alias="CONTENT_STYLE")
    content_format: str = Field("короткий пост", alias="CONTENT_FORMAT")
    content_length: str = Field("коротко", alias="CONTENT_LENGTH")
    content_variants: int = Field(1, alias="CONTENT_VARIANTS")

    morning_draft_time: str = Field("07:00", alias="MORNING_DRAFT_TIME")
    morning_publish_time: str = Field("08:00", alias="MORNING_PUBLISH_TIME")
    evening_draft_time: str = Field("19:00", alias="EVENING_DRAFT_TIME")
    evening_publish_time: str = Field("20:00", alias="EVENING_PUBLISH_TIME")
    scheduler_poll_seconds: int = Field(30, alias="SCHEDULER_POLL_SECONDS")

    def proxies(self) -> dict[str, str] | None:
        proxies: dict[str, str] = {}
        if self.http_proxy:
            proxies["http://"] = self.http_proxy
        if self.https_proxy:
            proxies["https://"] = self.https_proxy
        return proxies or None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
