from __future__ import annotations

import re

from utils.helpers import normalize_whitespace


class TextService:
    @staticmethod
    def clean_input(text: str) -> str:
        text = normalize_whitespace(text)
        text = re.sub(r"\n{4,}", "\n\n\n", text)
        return text.strip()

    @staticmethod
    def prepare_for_telegram(text: str) -> str:
        return normalize_whitespace(text)
