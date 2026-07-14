from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states.content_states import SimpleTopicStates
from config.settings import get_settings
from services.ai_service import AIService
from services.prompt_service import PromptService
from services.text_service import TextService
from utils.helpers import split_text

router = Router()
ai_service = AIService()
prompt_service = PromptService()
text_service = TextService()


@router.message(Command("reels"))
async def reels_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(SimpleTopicStates.topic)
    await message.answer("Напиши тему для идей Reels.")


@router.message(SimpleTopicStates.topic)
async def reels_topic(message: Message, state: FSMContext) -> None:
    topic = text_service.clean_input(message.text or "")
    prompt = prompt_service.build_reels_prompt(topic=topic, language=get_settings().default_language)
    await message.answer("Генерирую идеи...")
    result = await ai_service.chat(prompt, temperature=0.9)
    for chunk in split_text(result):
        await message.answer(chunk)
    await state.clear()
