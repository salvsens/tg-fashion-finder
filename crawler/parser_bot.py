import os
from aiogram import types
from core.database import add_raw_post

# Загружаем ID каналов один раз при импорте модуля
raw_channels = os.getenv("CHANNEL_IDS", "")
CHANNELS = [int(id.strip()) for id in raw_channels.split(",") if id.strip()]


async def handle_channel_post(message: types.Message):
    # Проверяем, что пост пришел из списка наших каналов
    if message.chat.id in CHANNELS:
        text = message.text or message.caption or ""

        photo_id = ""
        if message.photo:
            photo_id = message.photo[-1].file_id

        # Формируем имя канала для логов и отображения
        if message.chat.username:
            channel_name = message.chat.title
        else:
            channel_name = f"{message.chat.title} (ID: {message.chat.id})"

        # Генерируем прямую ссылку на пост
        post_url = message.get_url()

        # Передаем новый аргумент post_url в функцию БД
        await add_raw_post(
            channel=channel_name,
            text=text,
            img=photo_id,
            post_url=post_url
        )