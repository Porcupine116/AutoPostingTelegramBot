from aiogram.fsm.state import State, StatesGroup


class GenerateStates(StatesGroup):
    topic = State()
    style = State()
    format_name = State()
    length = State()
    variants = State()


class RewriteStates(StatesGroup):
    text = State()
    mode = State()
    style = State()


class SimpleTopicStates(StatesGroup):
    topic = State()


class ScriptStates(StatesGroup):
    topic = State()
    duration = State()
