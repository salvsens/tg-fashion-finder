import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from dotenv import load_dotenv

from database import init_db, add_raw_post

# 1. Загрузка переменных окружений из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

raw_channels = os.getenv("CHANNEL_IDS", "")
CHANNELS = [int(id.strip()) for id in raw_channels.split(",") if id.strip()]

dp = Dispatcher()


# Обработчик сообщений из каналов
@dp.channel_post()
async def handle_channel_post(message: types.Message):
    # Проверяем, что пост пришел из списка наших каналов
    if message.chat.id in CHANNELS:
        # Извлекаем текст (он может быть в тексте или в подписи к фото)
        text = message.text or message.caption or ""

        # Извлекаем фото (берем самое лучшее качество)
        photo_id = ""
        if message.photo:
            photo_id = message.photo[-1].file_id

        # Сохраняем в database.py
        # В качестве названия канала берем его заголовок или юзернейм
        if message.chat.username:
            channel_name = f"{message.chat.title} (https://t.me/{message.chat.username})"
        else:
            channel_name = f"{message.chat.title} (ID: {message.chat.id})"

        await add_raw_post (
            channel=channel_name,
            text=text,
            img=photo_id
        )

        print(f"Пост из канала '{channel_name}' сохранен в базу!")


async def main():
    # Настраиваем логирование, чтобы видеть ошибки
    logging.basicConfig(level=logging.INFO)

    # Инициализируем базу данных (создаем таблицу, если её нет)
    await init_db()

    bot = Bot(token=TOKEN)
    print("Парсер запущен и просматривает каналы...")

    # Запускаем получение обновлений
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")