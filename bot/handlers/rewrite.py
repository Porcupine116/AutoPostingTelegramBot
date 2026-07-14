from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.common import REWRITE_LABELS, style_keyboard, rewrite_keyboard
from bot.states.content_states import RewriteStates
from config.settings import get_settings
from services.ai_service import AIService
from services.prompt_service import PromptService
from services.text_service import TextService
from utils.helpers import split_text

router = Router()
ai_service = AIService()
prompt_service = PromptService()
text_service = TextService()


@router.message(Command("rewrite"))
async def rewrite_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(RewriteStates.text)
    await message.answer("Пришли текст, который нужно переписать.")


@router.message(RewriteStates.text)
async def rewrite_text(message: Message, state: FSMContext) -> None:
    await state.update_data(text=text_service.clean_input(message.text or ""))
    await state.set_state(RewriteStates.mode)
    await message.answer("Выбери, как переписать.", reply_markup=rewrite_keyboard("rw_mode"))


@router.callback_query(F.data.startswith("rw_mode:"), RewriteStates.mode)
async def rewrite_mode(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    mode_code = call.data.split(":", 1)[1]
    await state.update_data(mode=REWRITE_LABELS.get(mode_code, mode_code))
    await state.set_state(RewriteStates.style)
    await call.message.answer("Выбери стиль переписывания.", reply_markup=style_keyboard("rw_style"))


@router.callback_query(F.data.startswith("rw_style:"), RewriteStates.style)
async def rewrite_style(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    data = await state.get_data()
    style_code = call.data.split(":", 1)[1]
    prompt = prompt_service.build_rewrite_prompt(
        text=data["text"],
        mode=data["mode"],
        style=style_code,
        language=get_settings().default_language,
    )
    await call.message.answer("Переписываю текст...")
    result = await ai_service.chat(prompt)
    for chunk in split_text(result):
        await call.message.answer(chunk)
    await state.clear()
