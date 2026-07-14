from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

STYLE_OPTIONS = [
    ("Экспертный", "expert"),
    ("Простой и человеческий", "simple"),
    ("Цепляющий", "catchy"),
]

FORMAT_OPTIONS = [
    ("Короткий пост", "short"),
    ("Длинный пост", "long"),
    ("Продающий пост", "sales"),
    ("Прогрев", "warmup"),
    ("Карусель", "carousel"),
    ("Сторис", "stories"),
    ("Threads", "threads"),
    ("Reels / видео", "reels"),
]

LENGTH_OPTIONS = [
    ("Коротко", "short"),
    ("Средне", "medium"),
    ("Подробно", "long"),
]

REWRITE_MODES = [
    ("Проще", "simpler"),
    ("Экспертнее", "more_expert"),
    ("Цепляюще", "more_catchy"),
    ("Сократить", "shorter"),
    ("Расширить", "longer"),
]

CTA_TYPES = [
    ("Мягкий CTA", "soft"),
    ("Обычный CTA", "normal"),
    ("Продающий CTA", "sales"),
]

STYLE_LABELS = dict(STYLE_OPTIONS)
FORMAT_LABELS = dict(FORMAT_OPTIONS)
LENGTH_LABELS = dict(LENGTH_OPTIONS)
REWRITE_LABELS = dict(REWRITE_MODES)
CTA_LABELS = dict(CTA_TYPES)


def _keyboard(options: list[tuple[str, str]], prefix: str, row_width: int = 2) -> InlineKeyboardMarkup:
    buttons = [InlineKeyboardButton(text=text, callback_data=f"{prefix}:{value}") for text, value in options]
    rows = [buttons[i:i + row_width] for i in range(0, len(buttons), row_width)]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def style_keyboard(prefix: str = "style") -> InlineKeyboardMarkup:
    return _keyboard(STYLE_OPTIONS, prefix)


def format_keyboard(prefix: str = "format") -> InlineKeyboardMarkup:
    return _keyboard(FORMAT_OPTIONS, prefix, row_width=2)


def length_keyboard(prefix: str = "length") -> InlineKeyboardMarkup:
    return _keyboard(LENGTH_OPTIONS, prefix)


def variants_keyboard(prefix: str = "variants") -> InlineKeyboardMarkup:
    options = [("1", "1"), ("3", "3"), ("5", "5")]
    return _keyboard(options, prefix)


def rewrite_keyboard(prefix: str = "rewrite_mode") -> InlineKeyboardMarkup:
    return _keyboard(REWRITE_MODES, prefix, row_width=2)


def cta_keyboard(prefix: str = "cta") -> InlineKeyboardMarkup:
    return _keyboard(CTA_TYPES, prefix)
