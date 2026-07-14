from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ContentRequest:
    topic: str
    style: str
    format_name: str
    length: str
    variants: int
    language: str = "ru"


class PromptService:
    @staticmethod
    def build_generation_prompt(req: ContentRequest) -> str:
        return f"""
Ты — сильный контент-мейкер для Telegram-канала на тему авто, ДТП, страховых выплат, автоюриста и судебной практики.

Сделай {req.variants} вариант(а/ов) текста по теме: {req.topic}

Требования:
- язык: {req.language}
- стиль: {req.style}
- формат: {req.format_name}
- длина: {req.length}
- пиши естественно, без ощущения шаблона
- без сложных юридических терминов, если это не нужно
- текст должен быть пригоден для Telegram
- не пиши лишних пояснений вокруг текста
- если это автопост, текст должен читаться как готовый пост для канала

Верни только готовые варианты, каждый с новой строки и с понятным разделением.
""".strip()

    @staticmethod
    def build_rewrite_prompt(text: str, mode: str, style: str, language: str = "ru") -> str:
        return f"""
Перепиши текст по правилам:

Режим: {mode}
Стиль: {style}
Язык: {language}

Что нужно:
- сохранить смысл
- сделать текст читабельным
- убрать сухость и канцелярит
- если режим про сокращение — сократи без потери смысла
- если режим про расширение — добавь полезные детали без воды
- если режим про простоту — объясни человеческим языком

Текст:
{text}
""".strip()

    @staticmethod
    def build_titles_prompt(topic: str, count: int, style: str, language: str = "ru") -> str:
        return f"""
Сгенерируй {count} заголовков для Telegram-поста.

Тема: {topic}
Стиль канала: {style}
Язык: {language}

Требования:
- заголовки цепляющие, но без перегиба в кликбейт
- подойдут для канала про ДТП, страхование, автоюриста и судебную практику
- каждый заголовок с новой строки
- без пояснений и лишнего текста
""".strip()

    @staticmethod
    def build_cta_prompt(topic: str, cta_type: str, language: str = "ru") -> str:
        return f"""
Сгенерируй CTA для Telegram-поста.

Тема: {topic}
Тип CTA: {cta_type}
Язык: {language}

Нужно:
- сделать 5 вариантов
- текст короткий, естественный и уместный
- без агрессивных продаж
- каждый вариант с новой строки
""".strip()

    @staticmethod
    def build_reels_prompt(topic: str, language: str = "ru") -> str:
        return f"""
Придумай 5 идей для Reels/коротких видео по теме: {topic}
Язык: {language}

Для каждой идеи укажи:
- хук в начале
- краткую суть
- финальный призыв к действию

Пиши коротко, понятно и практично.
""".strip()

    @staticmethod
    def build_script_prompt(topic: str, duration: str, language: str = "ru") -> str:
        return f"""
Напиши сценарий для короткого видео/Reels.

Тема: {topic}
Длительность: {duration}
Язык: {language}

Нужно:
- хук в первые 1-2 секунды
- основной текст
- финальный CTA
- разговорный и естественный тон
- без перегруза юридическими терминами
""".strip()
