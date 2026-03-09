"""
Модуль машинной логики для fashion-бота.
Обрабатывает посты: извлекает цену и определяет категорию.
"""

import sys
import re
from pathlib import Path

# Добавляем корневую папку проекта в путь
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Импортируем функции для работы с БД
try:
    from bot.database import get_unprocessed_posts, update_post_data
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

def extract_price(text: str) -> int:
    """Извлекает цену из текста поста."""
    if not text:
        return 0
    
    text = text.lower()
    
    patterns = [
        r'(\d+)[\s]?(?:₽|руб|рублей|рубля|р\.?)',
        r'(?:₽|руб|рублей|рубля|р\.?)[\s]*(\d+)',
        r'цена[:\s]*(\d+)',
    ]
    
    # Сначала ищем явные цены
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            for group in match.groups():
                if group and group.isdigit():
                    price = int(group)
                    if 10 < price < 1000000:
                        return price
    
    # Если не нашли, ищем числа от 100 до 1000000
    numbers = re.findall(r'\b(\d{3,6})\b', text)
    if numbers:
        return int(numbers[0])
    
    return 0

def detect_category(text: str) -> str:
    """Определяет категорию одежды по ключевым словам."""
    if not text:
        return 'other'
    
    text_lower = text.lower()
    
    categories = {
        'shoes': ['кеды', 'кроссовки', 'обувь', 'ботинки', 'туфли', 'sneakers', 'nike', 'adidas', 'найк', 'адидас'],
        'hoodie': ['худи', 'толстовка', 'свитшот', 'кофта', 'олимпийка', 'hoodie'],
        'outerwear': ['куртка', 'пуховик', 'пальто', 'ветровка', 'бомбер', 'jacket'],
        'pants': ['штаны', 'джинсы', 'брюки', 'чиносы', 'карго', 'jeans'],
        't-shirt': ['футболка', 'майка', 'лонгслив', 'поло', 't-shirt'],
        'accessories': ['шапка', 'кепка', 'шарф', 'ремень', 'сумка', 'рюкзак']
    }
    
    matches = {cat: 0 for cat in categories}
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text_lower:
                matches[category] += 1
    
    best_category = 'other'
    max_matches = 0
    
    for category, count in matches.items():
        if count > max_matches:
            max_matches = count
            best_category = category
    
    return best_category if max_matches > 0 else 'other'

def process_text(text: str):
    """Обрабатывает один текст и возвращает цену и категорию."""
    price = extract_price(text)
    category = detect_category(text)
    return price, category

async def process_posts():
    """Обрабатывает все необработанные посты в базе данных."""
    if not DB_AVAILABLE:
        return
    
    unprocessed = await get_unprocessed_posts()
    
    if not unprocessed:
        return
    
    for post_id, raw_text in unprocessed:
        price = extract_price(raw_text)
        category = detect_category(raw_text)
        await update_post_data(post_id, price, category)

if __name__ == "__main__":
    # Функции доступны для импорта
    pass
