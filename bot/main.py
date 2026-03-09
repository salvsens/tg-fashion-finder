import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from core.database import init_db, search_items

from crawler.parser_bot import handle_channel_post

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandObject

import re

# 1. Загрузка переменных окружений из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 2. Настройка логирования, чтобы видеть ошибки в Docker
logging.basicConfig(level=logging.INFO)

# 3. Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.channel_post.register(handle_channel_post)
print("DEBUG: Хендлер каналов успешно зарегистрирован!")

def get_like_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="❤️ Лайк", callback_data="like_pressed")
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я Fashion Daemon bot.\n"
        "Я ищу лучшие предложения в fashion-каналах.\n"
        "Используй /search чтобы ракнуть дрипчик."
    )

@dp.message(Command("search"))
async def cmd_search(message: types.Message, command: CommandObject):
    user_query = command.args
    if not user_query:
        await message.answer("Введи запрос, например: <code>/search футболка</code>", parse_mode="HTML")
        return

    items = await search_items(search_query=user_query)

    if not items:
        await message.answer(f"По запросу «{user_query}» ничего не нашлось")
        return

    # Выводим до 5 постов
    for item in items[:5]:
        channel_info, raw_text, img, price = item

        # Название
        lines = raw_text.split('\n')
        item_name = lines[0][:50]

        #URL сообщения
        url_match = re.search(r'\((https://[^\)]+)\)', channel_info)
        clean_url = url_match.group(1) if url_match else "#"

        #название канала
        channel_name = channel_info.split('(')[0].strip()

        #формат сообщения
        caption = (
            f"<b>{item_name}</b>\n"
            f"💰 Цена: {price} ₽\n\n"
            f"🔗 Источник: <a href='{clean_url}'>{channel_name}</a>"
        )

        if img:
            await message.answer_photo(
                photo=img,
                caption=caption,
                parse_mode="HTML",
                reply_markup=get_like_keyboard()
            )
        else:
            await message.answer(
                text=caption,
                parse_mode="HTML",
                reply_markup=get_like_keyboard()
            )

@dp.callback_query(lambda c: c.data == "like_pressed")
async def process_like(callback: types.CallbackQuery):
    #пока просто уведомление
    await callback.answer("Добавлено в избранное! ✨", show_alert=False)

#Запуск

async def main():
    # Инициализируем БД
    await init_db()
    
    # Запуск поллинга
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot, allowed_updates=["message", "channel_post"])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")