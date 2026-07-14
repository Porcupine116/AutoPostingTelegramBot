from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class HistoryItem:
    user_id: int
    request_type: str
    prompt: str
    response: str
    style: str | None = None
    format_name: str | None = None


class HistoryService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    request_type TEXT NOT NULL,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    style TEXT,
                    format_name TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def save(self, item: HistoryItem) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO requests (
                    user_id, request_type, prompt, response, style, format_name, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.user_id,
                    item.request_type,
                    item.prompt,
                    item.response,
                    item.style,
                    item.format_name,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
