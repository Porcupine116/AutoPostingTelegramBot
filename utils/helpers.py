from __future__ import annotations

import re
from html import escape
from typing import Iterable

from config.settings import get_settings


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\t ]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def escape_html_text(text: str) -> str:
    return escape(text, quote=False)


def split_text(text: str, limit: int | None = None) -> list[str]:
    settings = get_settings()
    limit = limit or settings.max_message_length
    text = normalize_whitespace(text)
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    current = ""
    paragraphs = text.split("\n\n")

    for paragraph in paragraphs:
        candidate = paragraph if not current else current + "\n\n" + paragraph
        if len(candidate) <= limit:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(paragraph) <= limit:
            current = paragraph
            continue

        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        buffer = ""
        for sentence in sentences:
            candidate = sentence if not buffer else buffer + " " + sentence
            if len(candidate) <= limit:
                buffer = candidate
            else:
                if buffer:
                    chunks.append(buffer)
                if len(sentence) <= limit:
                    buffer = sentence
                else:
                    for i in range(0, len(sentence), limit):
                        piece = sentence[i:i + limit]
                        if len(piece) == limit:
                            chunks.append(piece)
                        else:
                            buffer = piece
        current = buffer

    if current:
        chunks.append(current)
    return chunks


def join_non_empty(parts: Iterable[str], sep: str = "\n") -> str:
    return sep.join(part for part in parts if part and part.strip())
