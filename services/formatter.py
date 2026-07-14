from __future__ import annotations

from utils.helpers import escape_html_text


class Formatter:
    @staticmethod
    def format_single_result(title: str, body: str) -> str:
        safe_title = escape_html_text(title)
        safe_body = escape_html_text(body)
        return f"<b>{safe_title}</b>\n\n{safe_body}"

    @staticmethod
    def format_multiple_results(items: list[str], heading: str) -> str:
        blocks = []
        for idx, item in enumerate(items, start=1):
            blocks.append(f"<b>{escape_html_text(heading)} {idx}</b>\n\n{escape_html_text(item)}")
        return "\n\n".join(blocks)
