from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.common import STYLE_LABELS, style_keyboard, variants_keyboard
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


@router.message(Command("titles"))
async def titles_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(SimpleTopicStates.topic)
    await message.answer("Напиши тему для заголовков.")


@router.message(SimpleTopicStates.topic)
async def titles_topic(message: Message, state: FSMContext) -> None:
    await state.update_data(topic=text_service.clean_input(message.text or ""))
    await message.answer("Выбери стиль.", reply_markup=style_keyboard("title_style"))


@router.callback_query(F.data.startswith("title_style:"))
async def titles_style(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    style_code = call.data.split(":", 1)[1]
    await state.update_data(style=STYLE_LABELS.get(style_code, style_code))
    await call.message.answer("Сколько заголовков сделать?", reply_markup=variants_keyboard("title_count"))


@router.callback_query(F.data.startswith("title_count:"))
async def titles_count(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    count = int(call.data.split(":", 1)[1])
    data = await state.get_data()
    prompt = prompt_service.build_titles_prompt(
        topic=data["topic"],
        count=count,
        style=data.get("style", get_settings().default_style),
        language=get_settings().default_language,
    )
    await call.message.answer("Генерирую заголовки...")
    result = await ai_service.chat(prompt, temperature=0.8)
    for chunk in split_text(result):
        await call.message.answer(chunk)
    await state.clear()
