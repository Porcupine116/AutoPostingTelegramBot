from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

router = Router()

COMMAND_MAP = {
    "/generate": "Используй команду /generate",
    "/rewrite": "Используй команду /rewrite",
    "/titles": "Используй команду /titles",
    "/cta": "Используй команду /cta",
    "/reels": "Используй команду /reels",
    "/script": "Используй команду /script",
    "/autopost": "Используй команду /autopost",
    "/settings": "Используй команду /settings",
    "/help": "Используй команду /help",
}


@router.callback_query(F.data.startswith("menu:"))
async def menu_router(call: CallbackQuery) -> None:
    await call.answer()
    cmd = call.data.split(":", 1)[1]
    text = COMMAND_MAP.get(cmd, "Неизвестная команда")
    await call.message.answer(text)
