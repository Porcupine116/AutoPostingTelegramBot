from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.common import CTA_LABELS, cta_keyboard
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


@router.message(Command("cta"))
async def cta_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(SimpleTopicStates.topic)
    await message.answer("Напиши тему или контекст для CTA.")


@router.message(SimpleTopicStates.topic)
async def cta_topic(message: Message, state: FSMContext) -> None:
    await state.update_data(topic=text_service.clean_input(message.text or ""))
    await message.answer("Выбери тип CTA.", reply_markup=cta_keyboard("cta_type"))


@router.callback_query(F.data.startswith("cta_type:"))
async def cta_type(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    cta_type_code = call.data.split(":", 1)[1]
    data = await state.get_data()
    prompt = prompt_service.build_cta_prompt(
        topic=data["topic"],
        cta_type=CTA_LABELS.get(cta_type_code, cta_type_code),
        language=get_settings().default_language,
    )
    await call.message.answer("Генерирую CTA...")
    result = await ai_service.chat(prompt, temperature=0.8)
    for chunk in split_text(result):
        await call.message.answer(chunk)
    await state.clear()
