from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states.content_states import ScriptStates
from config.settings import get_settings
from services.ai_service import AIService
from services.prompt_service import PromptService
from services.text_service import TextService
from utils.helpers import split_text

router = Router()
ai_service = AIService()
prompt_service = PromptService()
text_service = TextService()


@router.message(Command("script"))
async def script_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(ScriptStates.topic)
    await message.answer("Напиши тему для сценария.")


@router.message(ScriptStates.topic)
async def script_topic(message: Message, state: FSMContext) -> None:
    await state.update_data(topic=text_service.clean_input(message.text or ""))
    await state.set_state(ScriptStates.duration)
    await message.answer("Укажи длительность, например: 15 секунд, 30 секунд, 60 секунд.")


@router.message(ScriptStates.duration)
async def script_duration(message: Message, state: FSMContext) -> None:
    duration = text_service.clean_input(message.text or "")
    data = await state.get_data()
    prompt = prompt_service.build_script_prompt(
        topic=data["topic"],
        duration=duration,
        language=get_settings().default_language,
    )
    await message.answer("Пишу сценарий...")
    result = await ai_service.chat(prompt, temperature=0.85)
    for chunk in split_text(result):
        await message.answer(chunk)
    await state.clear()
