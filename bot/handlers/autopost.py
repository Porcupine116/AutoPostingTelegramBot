from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from config.settings import get_settings
from services.autoposting import AutoPostManager

router = Router()
manager: AutoPostManager | None = None


def set_autopost_manager(value: AutoPostManager) -> None:
    global manager
    manager = value


@router.message(Command("autopost"))
async def autopost_status(message: Message) -> None:
    settings = get_settings()
    await message.answer(
        "Автопостинг сейчас настроен так:\n"
        f"Режим: {settings.autopost_mode}\n"
        f"Черновик утром: {settings.morning_draft_time}\n"
        f"Публикация утром: {settings.morning_publish_time}\n"
        f"Черновик вечером: {settings.evening_draft_time}\n"
        f"Публикация вечером: {settings.evening_publish_time}\n\n"
        "Режимы:\n"
        "- approve — сначала одобрение, потом публикация\n"
        "- auto — публикация без одобрения"
    )


@router.callback_query(F.data.startswith("ap:regen:"))
async def regenerate(call: CallbackQuery) -> None:
    await call.answer("Перегенерирую...")
    if manager is None:
        if call.message:
            await call.message.answer("Менеджер автопостинга не инициализирован.")
        return
    post_id = int(call.data.split(":", 2)[2])
    await manager.regenerate(
        post_id,
        message_chat_id=call.message.chat.id if call.message else None,
        message_id=call.message.message_id if call.message else None,
    )


@router.callback_query(F.data.startswith("ap:approve:"))
async def approve(call: CallbackQuery) -> None:
    await call.answer("Одобрено")
    if manager is None:
        if call.message:
            await call.message.answer("Менеджер автопостинга не инициализирован.")
        return
    post_id = int(call.data.split(":", 2)[2])
    await manager.approve(post_id)
    if call.message:
        await call.message.answer(f"✅ Пост #{post_id} одобрен. Он уйдёт в канал по времени публикации.")


@router.callback_query(F.data.startswith("ap:publish:"))
async def publish_now(call: CallbackQuery) -> None:
    await call.answer("Публикую сейчас")
    if manager is None:
        if call.message:
            await call.message.answer("Менеджер автопостинга не инициализирован.")
        return
    post_id = int(call.data.split(":", 2)[2])
    await manager.publish_now(post_id)
    if call.message:
        await call.message.answer(f"🚀 Пост #{post_id} отправлен в канал.")


@router.callback_query(F.data.startswith("ap:skip:"))
async def skip(call: CallbackQuery) -> None:
    await call.answer("Пропущено")
    if manager is None:
        if call.message:
            await call.message.answer("Менеджер автопостинга не инициализирован.")
        return
    post_id = int(call.data.split(":", 2)[2])
    await manager.skip(post_id)
    if call.message:
        await call.message.answer(f"🗑 Пост #{post_id} пропущен.")
