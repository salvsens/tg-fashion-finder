import asyncio
import logging
import os
import html
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from core.database import init_db, search_items

from crawler.parser_bot import handle_channel_post

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import CommandObject

# 1. Загрузка переменных окружений из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# 2. Настройка логирования, чтобы видеть ошибки в Docker
logging.basicConfig(level=logging.INFO)

# 3. Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.channel_post.register(handle_channel_post)

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
        channel_info, post_url, raw_text, image_url, price = item

        # 1. Защита от старых записей в БД (где может быть NULL/None)
        raw_text = raw_text or "Без описания"
        post_url = post_url or "https://t.me"
        channel_info = channel_info or "Неизвестный канал"

        if price and price > 0:
            price_text = f"💰 Цена: {price} ₽"
        else:
            price_text = "❌ <b>Продано</b>"

        # 2. Получение названия
        lines = raw_text.split('\n')
        item_name = lines[0][:50] if lines and lines[0] else "Товар без названия"

        # 3. ЭКРАНИРОВАНИЕ HTML (Главная причина молчания бота)
        # Превращает < и > в безопасные &lt; и &gt;
        safe_item_name = html.escape(item_name)

        channel_name = channel_info.split('(')[0].strip()
        safe_channel_name = html.escape(channel_name)

        # Формат сообщения с безопасными переменными
        caption = (
            f"<b>{safe_item_name}</b>\n"
            f"{price_text}\n\n"
            f"🔗 Источник: <a href='{post_url}'>{safe_channel_name}</a>"
        )

        try:
            if image_url:
                await message.answer_photo(
                    photo=image_url,
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
        except Exception as e:
            print(f"Ошибка отправки поста: {e}")

@dp.callback_query(lambda c: c.data == "like_pressed")
async def process_like(callback: types.CallbackQuery):
    #пока просто уведомление
    await callback.answer("Добавлено в избранное! ✨", show_alert=False)

async def scheduler():
    from ml_logic.processor import process_posts
    while True:
        try:
            print("LOG: Запуск фоновой обработки постов...")
            await process_posts()
        except Exception as e:
            print(f"ERROR в планировщике: {e}")

        # Ждем 5 минут перед следующей проверкой
        await asyncio.sleep(300)

#Запуск

async def main():
    # Инициализируем БД
    await init_db()

    asyncio.create_task(scheduler())

    # Запуск поллинга
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot, allowed_updates=["message", "channel_post"])

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен")