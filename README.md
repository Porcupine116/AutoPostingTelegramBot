# Telegram Auto Content Bot

Простой Telegram-бот на Python 3.11+ для генерации постов через OpenRouter.

## Что умеет
- /generate — генерация поста
- /rewrite — переписывание текста
- /titles — заголовки
- /cta — CTA
- /reels — идеи для Reels
- /script — сценарий видео
- /autopost — статус автопостинга
- /settings — настройки
- /help — помощь

## Запуск
1. Скопируй `.env.example` в `.env`
2. Заполни `BOT_TOKEN` и `OPENROUTER_API_KEY`
3. Если нужен автопостинг, заполни:
   - `ADMIN_CHAT_ID`
   - `CHANNEL_ID`
   - `AUTOPOST_MODE=approve` или `AUTOPOST_MODE=auto`
4. Установи зависимости:
   ```bash
   pip install -r requirements.txt
   ```
5. Запусти:
   ```bash
   python main.py
   ```

## Автопостинг
Бот создает черновики по расписанию:
- утром: `MORNING_DRAFT_TIME` -> `MORNING_PUBLISH_TIME`
- вечером: `EVENING_DRAFT_TIME` -> `EVENING_PUBLISH_TIME`

Режимы:
- `approve` — бот присылает черновик в админ-чат, там можно одобрить, перегенерировать или опубликовать сразу
- `auto` — бот сам публикует в канал без одобрения

## Примечание
История запросов и расписание хранятся в SQLite (`data/history.sqlite3`).
