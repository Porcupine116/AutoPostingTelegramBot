from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from config.settings import get_settings
from services.scheduled_posts_service import build_daily_slots

router = Router()


@router.message(Command("settings"))
async def settings_cmd(message: Message) -> None:
    settings = get_settings()
    slots = build_daily_slots()
    await message.answer(
        "Текущие настройки по умолчанию:\n"
        f"Стиль: {settings.default_style}\n"
        f"Формат: {settings.default_format}\n"
        f"Язык: {settings.default_language}\n"
        f"Модель: {settings.openrouter_model}\n"
        f"Автопостинг: {settings.autopost_mode}\n"
        f"Канал: {settings.channel_id or 'не задан'}\n"
        f"Админ-чат: {settings.admin_chat_id or 'не задан'}\n"
        f"Утро: {settings.morning_draft_time} -> {settings.morning_publish_time}\n"
        f"Вечер: {settings.evening_draft_time} -> {settings.evening_publish_time}\n\n"
        f"Ближайшие слоты: {slots[0][1].isoformat()} / {slots[0][2].isoformat()}\n"
        f"{slots[1][1].isoformat()} / {slots[1][2].isoformat()}"
    )
