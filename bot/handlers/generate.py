from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.keyboards.common import (
    FORMAT_LABELS,
    LENGTH_LABELS,
    STYLE_LABELS,
    format_keyboard,
    length_keyboard,
    style_keyboard,
    variants_keyboard,
)
from bot.states.content_states import GenerateStates
from config.settings import get_settings
from services.ai_service import AIService
from services.history_service import HistoryItem, HistoryService
from services.prompt_service import ContentRequest, PromptService
from services.text_service import TextService
from utils.helpers import split_text

router = Router()
ai_service = AIService()
prompt_service = PromptService()
text_service = TextService()
history_service = HistoryService(get_settings().database_path)


@router.message(Command("generate"))
async def generate_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(GenerateStates.topic)
    await message.answer("Напиши тему поста.")


@router.message(GenerateStates.topic)
async def generate_topic(message: Message, state: FSMContext) -> None:
    await state.update_data(topic=text_service.clean_input(message.text or ""))
    await state.set_state(GenerateStates.style)
    await message.answer("Выбери стиль.", reply_markup=style_keyboard("gen_style"))


@router.callback_query(F.data.startswith("gen_style:"), GenerateStates.style)
async def generate_style(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    style_code = call.data.split(":", 1)[1]
    await state.update_data(style=STYLE_LABELS.get(style_code, style_code))
    await state.set_state(GenerateStates.format_name)
    await call.message.answer("Выбери формат.", reply_markup=format_keyboard("gen_format"))


@router.callback_query(F.data.startswith("gen_format:"), GenerateStates.format_name)
async def generate_format(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    format_code = call.data.split(":", 1)[1]
    await state.update_data(format_name=FORMAT_LABELS.get(format_code, format_code))
    await state.set_state(GenerateStates.length)
    await call.message.answer("Выбери длину.", reply_markup=length_keyboard("gen_length"))


@router.callback_query(F.data.startswith("gen_length:"), GenerateStates.length)
async def generate_length(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    length_code = call.data.split(":", 1)[1]
    await state.update_data(length=LENGTH_LABELS.get(length_code, length_code))
    await state.set_state(GenerateStates.variants)
    await call.message.answer("Сколько вариантов сделать?", reply_markup=variants_keyboard("gen_variants"))


@router.callback_query(F.data.startswith("gen_variants:"), GenerateStates.variants)
async def generate_variants(call: CallbackQuery, state: FSMContext) -> None:
    await call.answer()
    variants = int(call.data.split(":", 1)[1])
    data = await state.get_data()
    req = ContentRequest(
        topic=data["topic"],
        style=data["style"],
        format_name=data["format_name"],
        length=data["length"],
        variants=variants,
        language=get_settings().default_language,
    )
    prompt = prompt_service.build_generation_prompt(req)

    await call.message.answer("Готовлю текст...")
    result = await ai_service.chat(prompt)

    history_service.save(
        HistoryItem(
            user_id=call.from_user.id,
            request_type="generate",
            prompt=prompt,
            response=result,
            style=req.style,
            format_name=req.format_name,
        )
    )

    for chunk in split_text(result):
        await call.message.answer(chunk)
    await state.clear()
