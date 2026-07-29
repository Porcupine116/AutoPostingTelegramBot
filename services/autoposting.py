from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from html import escape

from aiogram import Bot
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config.settings import get_settings
from services.ai_service import AIService, AIServiceError
from services.history_service import HistoryItem, HistoryService
from services.prompt_service import ContentRequest, PromptService
from services.scheduled_posts_service import ScheduledPost, ScheduledPostService, build_daily_slots
from utils.helpers import split_text

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class AutopostContext:
    bot: Bot
    ai_service: AIService
    prompt_service: PromptService
    history_service: HistoryService
    scheduled_posts: ScheduledPostService


class AutoPostManager:
    def __init__(self, ctx: AutopostContext) -> None:
        self.ctx = ctx
        self.settings = get_settings()
        self._task: asyncio.Task[None] | None = None

    def start(self) -> asyncio.Task[None]:
        if self._task and not self._task.done():
            return self._task
        self._task = asyncio.create_task(self._run_loop(), name="autopost-scheduler")
        return self._task

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run_loop(self) -> None:
        logger.info("Autopost scheduler started")
        while True:
            try:
                await self.sync_daily_plan()
                await self.process_due_drafts()
                await self.process_due_publications()
            except Exception:
                logger.exception("Autopost scheduler error")
            await asyncio.sleep(max(5, self.settings.scheduler_poll_seconds))

    async def sync_daily_plan(self) -> None:
        if not self.settings.channel_id:
            logger.warning("CHANNEL_ID is not configured")
            return

        mode = (self.settings.autopost_mode or "approve").lower()

        # В approve-режиме нужен админ-чат, иначе черновик некому показывать и нечего одобрять.
        if mode != "auto" and not self.settings.admin_chat_id:
            logger.warning("AUTOPOST_MODE=approve, but ADMIN_CHAT_ID is not configured")
            return

        slots = build_daily_slots()
        for slot_name, draft_at, publish_at in slots:
            self.ctx.scheduled_posts.create_slot_if_missing(
                slot_name=slot_name,
                draft_at=draft_at,
                publish_at=publish_at,
                topic=self.settings.content_topic,
                style=self.settings.content_style,
                format_name=self.settings.content_format,
                length=self.settings.content_length,
                variants=self.settings.content_variants,
                mode=mode,
            )

    async def process_due_drafts(self) -> None:
        due_posts = self.ctx.scheduled_posts.list_due_for_generation()
        for post in due_posts:
            await self._generate_and_notify(post)

    async def process_due_publications(self) -> None:
        due_posts = self.ctx.scheduled_posts.list_due_for_publication()
        for post in due_posts:
            await self._publish(post)

    async def _generate_and_notify(self, post: ScheduledPost) -> None:
        prompt = self.ctx.prompt_service.build_generation_prompt(
            ContentRequest(
                topic=post.topic,
                style=post.style,
                format_name=post.format_name,
                length=post.length,
                variants=post.variants,
                language=self.settings.default_language,
            )
        )
        try:
            content = await self.ctx.ai_service.chat(prompt)
        except AIServiceError as exc:
            logger.exception("Failed to generate post %s", post.id)
            self.ctx.scheduled_posts.mark_failed(post.id, str(exc))
            if self.settings.admin_chat_id:
                await self.ctx.bot.send_message(
                    self.settings.admin_chat_id,
                    f"Ошибка генерации поста #{post.id}: {escape(str(exc))}",
                )
            return

        status = "auto_ready" if post.mode == "auto" else "awaiting_approval"
        self.ctx.scheduled_posts.set_generated(post.id, content=content, prompt=prompt, status=status)

        if self.settings.admin_chat_id:
            text = (
                f"<b>Черновик #{post.id}</b>\n"
                f"Слот: {escape(post.slot_name)}\n"
                f"Тема: {escape(post.topic)}\n"
                f"Публикация: {escape(post.publish_at)}\n\n"
                f"{escape(content)}"
            )
            await self._send_chunked(self.settings.admin_chat_id, text, post.id)

    async def _publish(self, post: ScheduledPost) -> None:
        post = self.ctx.scheduled_posts.get(post.id)
        if post is None or not post.content:
            return

        if post.mode != "auto" and post.status != "approved":
            return

        channel_id = self.settings.channel_id
        if not channel_id:
            logger.warning("CHANNEL_ID is not configured")
            return

        try:
            sent_message_id: int | None = None
            for idx, chunk in enumerate(split_text(post.content)):
                sent = await self.ctx.bot.send_message(channel_id, chunk)
                if idx == 0:
                    sent_message_id = sent.message_id
            self.ctx.scheduled_posts.mark_published(post.id, channel_message_id=sent_message_id)
            self.ctx.history_service.save(
                HistoryItem(
                    user_id=0,
                    request_type=f"scheduled:{post.slot_name}",
                    prompt=post.prompt or "",
                    response=post.content,
                    style=post.style,
                    format_name=post.format_name,
                )
            )
            if self.settings.admin_chat_id:
                await self.ctx.bot.send_message(self.settings.admin_chat_id, f"✅ Пост #{post.id} опубликован в канал.")
        except Exception as exc:
            logger.exception("Failed to publish post %s", post.id)
            self.ctx.scheduled_posts.mark_failed(post.id, f"publish_error: {exc}")
            if self.settings.admin_chat_id:
                await self.ctx.bot.send_message(
                    self.settings.admin_chat_id,
                    f"Ошибка публикации поста #{post.id}: {escape(str(exc))}",
                )

    async def regenerate(self, post_id: int, message_chat_id: int | None = None, message_id: int | None = None) -> None:
        post = self.ctx.scheduled_posts.get(post_id)
        if post is None:
            return
        await self._generate_and_notify(post)
        refreshed = self.ctx.scheduled_posts.get(post_id)
        if refreshed and refreshed.content and message_chat_id and message_id:
            text = (
                f"<b>Черновик #{refreshed.id} обновлён</b>\n"
                f"Слот: {escape(refreshed.slot_name)}\n"
                f"Тема: {escape(refreshed.topic)}\n"
                f"Публикация: {escape(refreshed.publish_at)}\n\n"
                f"{escape(refreshed.content)}"
            )
            await self.ctx.bot.edit_message_text(
                chat_id=message_chat_id,
                message_id=message_id,
                text=text,
                reply_markup=self._draft_keyboard(post_id),
            )

    async def approve(self, post_id: int) -> None:
        self.ctx.scheduled_posts.approve(post_id)

    async def skip(self, post_id: int) -> None:
        self.ctx.scheduled_posts.skip(post_id)

    async def publish_now(self, post_id: int) -> None:
        post = self.ctx.scheduled_posts.get(post_id)
        if post is None:
            return
        self.ctx.scheduled_posts.approve(post_id)
        await self._publish(post)

    async def _send_chunked(self, chat_id: int | str, text: str, post_id: int) -> None:
        chunks = split_text(text)
        for idx, chunk in enumerate(chunks):
            if idx == 0:
                await self.ctx.bot.send_message(chat_id, chunk, reply_markup=self._draft_keyboard(post_id))
            else:
                await self.ctx.bot.send_message(chat_id, chunk)

    def _draft_keyboard(self, post_id: int) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 Перегенерировать", callback_data=f"ap:regen:{post_id}"),
                    InlineKeyboardButton(text="✅ Одобрить", callback_data=f"ap:approve:{post_id}"),
                ],
                [
                    InlineKeyboardButton(text="🚀 Опубликовать сейчас", callback_data=f"ap:publish:{post_id}"),
                    InlineKeyboardButton(text="🗑 Пропустить", callback_data=f"ap:skip:{post_id}"),
                ],
            ]
        )
