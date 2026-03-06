import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from core.database import init_db, search_items

from crawler.parser_bot import handle_channel_post

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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я Fashion Daemon bot.\n"
        "Я ищу лучшие предложения в fashion-каналах.\n"
        "Используй /search чтобы ракнуть дрипчик."
    )

@dp.message(Command("search"))
async def cmd_search(message: types.Message):
    # Тестовый запрос к базе данных
    items = await search_items()
    
    if not items:
        await message.answer("К сожалению, ниче не найдено")
        return

    for item in items[:5]:  # Вывод первых 5 предложений
        channel, text, img, price = item
        caption = f"Канал: {channel}\n💰 Цена: {price} ₽\n\n{text[:100]}..."
        
        if img:
            await message.answer_photo(photo=img, caption=caption)
        else:
            await message.answer(caption)

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