from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

router = Router()


def main_menu_keyboard():
    buttons = [
        ("Generate", "/generate"),
        ("Rewrite", "/rewrite"),
        ("Titles", "/titles"),
        ("CTA", "/cta"),
        ("Reels", "/reels"),
        ("Script", "/script"),
        ("Autopost", "/autopost"),
        ("Settings", "/settings"),
        ("Help", "/help"),
    ]
    b = [InlineKeyboardButton(text=text, callback_data=f"menu:{value}") for text, value in buttons]
    rows = [b[i:i + 2] for i in range(0, len(b), 2)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Привет. Я помогу генерировать посты, заголовки, CTA и сценарии для Telegram-канала.\n\n"
        "Теперь есть и автопостинг: можно генерировать черновики по расписанию, одобрять их кнопкой или публиковать сразу.\n\n"
        "Выбирай команду из меню ниже или пиши /help.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("help"))
async def help_cmd(message: Message) -> None:
    await message.answer(
        "/generate — генерация поста\n"
        "/rewrite — переписать текст\n"
        "/titles — заголовки\n"
        "/cta — CTA\n"
        "/reels — идеи для Reels\n"
        "/script — сценарий видео\n"
        "/autopost — статус автопостинга\n"
        "/settings — настройки\n"
        "/help — помощь",
        reply_markup=main_menu_keyboard(),
    )
