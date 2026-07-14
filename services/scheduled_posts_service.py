from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from config.settings import get_settings


@dataclass(slots=True)
class ScheduledPost:
    id: int
    slot_name: str
    status: str
    mode: str
    topic: str
    style: str
    format_name: str
    length: str
    variants: int
    draft_at: str
    publish_at: str
    content: str | None
    prompt: str | None
    admin_message_id: int | None
    channel_message_id: int | None
    error: str | None


class ScheduledPostService:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS scheduled_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slot_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    style TEXT NOT NULL,
                    format_name TEXT NOT NULL,
                    length TEXT NOT NULL,
                    variants INTEGER NOT NULL,
                    draft_at TEXT NOT NULL,
                    publish_at TEXT NOT NULL,
                    content TEXT,
                    prompt TEXT,
                    admin_message_id INTEGER,
                    channel_message_id INTEGER,
                    error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(slot_name, draft_at)
                )
                """
            )
            conn.commit()

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def create_slot_if_missing(
        self,
        *,
        slot_name: str,
        draft_at: datetime,
        publish_at: datetime,
        topic: str,
        style: str,
        format_name: str,
        length: str,
        variants: int,
        mode: str,
    ) -> int | None:
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id FROM scheduled_posts WHERE slot_name = ? AND draft_at = ?",
                (slot_name, draft_at.isoformat()),
            ).fetchone()
            if existing:
                return int(existing["id"])

            cursor = conn.execute(
                """
                INSERT INTO scheduled_posts (
                    slot_name, status, mode, topic, style, format_name, length, variants,
                    draft_at, publish_at, content, prompt, admin_message_id, channel_message_id,
                    error, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, ?, ?)
                """,
                (
                    slot_name,
                    "planned",
                    mode,
                    topic,
                    style,
                    format_name,
                    length,
                    variants,
                    draft_at.isoformat(),
                    publish_at.isoformat(),
                    self._now().isoformat(),
                    self._now().isoformat(),
                ),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def list_due_for_generation(self, now: datetime | None = None) -> list[ScheduledPost]:
        now = now or self._now()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM scheduled_posts
                WHERE status = 'planned' AND draft_at <= ?
                ORDER BY draft_at ASC
                """,
                (now.isoformat(),),
            ).fetchall()
            return [self._row_to_post(row) for row in rows]

    def list_due_for_publication(self, now: datetime | None = None) -> list[ScheduledPost]:
        now = now or self._now()
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM scheduled_posts
                WHERE publish_at <= ? AND status IN ('approved', 'auto_ready')
                ORDER BY publish_at ASC
                """,
                (now.isoformat(),),
            ).fetchall()
            return [self._row_to_post(row) for row in rows]

    def get(self, post_id: int) -> ScheduledPost | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM scheduled_posts WHERE id = ?", (post_id,)).fetchone()
            return self._row_to_post(row) if row else None

    def set_generated(
        self,
        post_id: int,
        *,
        content: str,
        prompt: str,
        status: str,
        error: str | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE scheduled_posts
                SET content = ?, prompt = ?, status = ?, error = ?, updated_at = ?
                WHERE id = ?
                """,
                (content, prompt, status, error, self._now().isoformat(), post_id),
            )
            conn.commit()

    def approve(self, post_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE scheduled_posts SET status = 'approved', updated_at = ? WHERE id = ?",
                (self._now().isoformat(), post_id),
            )
            conn.commit()

    def mark_auto_ready(self, post_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE scheduled_posts SET status = 'auto_ready', updated_at = ? WHERE id = ?",
                (self._now().isoformat(), post_id),
            )
            conn.commit()

    def mark_published(self, post_id: int, channel_message_id: int | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE scheduled_posts
                SET status = 'published', channel_message_id = COALESCE(?, channel_message_id), updated_at = ?
                WHERE id = ?
                """,
                (channel_message_id, self._now().isoformat(), post_id),
            )
            conn.commit()

    def mark_failed(self, post_id: int, error: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE scheduled_posts SET status = 'failed', error = ?, updated_at = ? WHERE id = ?",
                (error, self._now().isoformat(), post_id),
            )
            conn.commit()

    def skip(self, post_id: int) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE scheduled_posts SET status = 'skipped', updated_at = ? WHERE id = ?",
                (self._now().isoformat(), post_id),
            )
            conn.commit()

    def pending_summary(self, limit: int = 10) -> list[ScheduledPost]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM scheduled_posts
                WHERE status IN ('planned', 'awaiting_approval', 'approved', 'auto_ready')
                ORDER BY draft_at ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [self._row_to_post(row) for row in rows]

    def _row_to_post(self, row: sqlite3.Row | None) -> ScheduledPost | None:
        if row is None:
            return None
        return ScheduledPost(
            id=int(row["id"]),
            slot_name=row["slot_name"],
            status=row["status"],
            mode=row["mode"],
            topic=row["topic"],
            style=row["style"],
            format_name=row["format_name"],
            length=row["length"],
            variants=int(row["variants"]),
            draft_at=row["draft_at"],
            publish_at=row["publish_at"],
            content=row["content"],
            prompt=row["prompt"],
            admin_message_id=row["admin_message_id"],
            channel_message_id=row["channel_message_id"],
            error=row["error"],
        )


def parse_hhmm(value: str) -> time:
    hour, minute = value.split(":", 1)
    return time(hour=int(hour), minute=int(minute))


def next_occurrence(base_date: date, hhmm: str, tz: ZoneInfo) -> datetime:
    return datetime.combine(base_date, parse_hhmm(hhmm), tzinfo=tz)


def build_daily_slots(now: datetime | None = None) -> list[tuple[str, datetime, datetime]]:
    settings = get_settings()
    tz = ZoneInfo(settings.schedule_timezone)
    now = now or datetime.now(tz)
    today = now.astimezone(tz).date()

    morning = ("morning", next_occurrence(today, settings.morning_draft_time, tz), next_occurrence(today, settings.morning_publish_time, tz))
    evening = ("evening", next_occurrence(today, settings.evening_draft_time, tz), next_occurrence(today, settings.evening_publish_time, tz))

    if now.astimezone(tz) > evening[2]:
        tomorrow = today + timedelta(days=1)
        morning = ("morning", next_occurrence(tomorrow, settings.morning_draft_time, tz), next_occurrence(tomorrow, settings.morning_publish_time, tz))
        evening = ("evening", next_occurrence(tomorrow, settings.evening_draft_time, tz), next_occurrence(tomorrow, settings.evening_publish_time, tz))

    return [morning, evening]
