"""
Модуль машинной логики для fashion-бота.
Превращает сырые посты из каналов в структурированные данные с ценой и категорией.
"""

import sys
import os
import re
import asyncio
from pathlib import Path

# Добавляем корневую папку проекта в путь поиска модулей
# Поднимаемся на два уровня вверх: ml_logic/ -> fashion-bot/
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Импортируем функции Леонида из папки bot
from bot.database import get_unprocessed_posts, update_post_data

# ===== ТВОИ ФУНКЦИИ ОБРАБОТКИ =====

def extract_price(text: str) -> int:
    """
    Извлекает цену из текста поста.
    
    Аргументы:
        text: сырой текст поста
        
    Возвращает:
        int: найденная цена или 0
    """
    if not text:
        return 0
    
    text = text.lower()
    
    # Паттерны для поиска цены
    patterns = [
        r'(\d+)[\s]?(?:₽|руб|рублей|рубля|р\.?)',           # 1500₽, 1500 руб
        r'(?:₽|руб|рублей|рубля|р\.?)[\s]*(\d+)',           # ₽1500, руб1500
        r'цена[:\s]*(\d+)',                                  # цена: 1500
        r'(\d{3,6})\b',                                      # просто число от 100 до 999999
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Находим группу с числом
            for group in match.groups():
                if group and group.isdigit():
                    price = int(group)
                    # Проверяем, что цена реалистичная
                    if 10 < price < 1000000:
                        return price
    
    return 0

def detect_category(text: str) -> str:
    """
    Определяет категорию одежды по ключевым словам.
    
    Аргументы:
        text: сырой текст поста
        
    Возвращает:
        str: категория (shoes, hoodie, outerwear, pants, t-shirt, accessories, other)
    """
    if not text:
        return 'other'
    
    text_lower = text.lower()
    
    # Словарь категорий с ключевыми словами
    categories = {
        'shoes': [
            'кеды', 'кроссовки', 'обувь', 'ботинки', 'туфли', 
            'sneakers', 'converse', 'nike', 'adidas', 'new balance', 
            'vans', 'найк', 'адидас', 'рибок'
        ],
        'hoodie': [
            'худи', 'толстовка', 'свитшот', 'кофта', 'олимпийка', 
            'hoodie', 'толстовка с капюшоном'
        ],
        'outerwear': [
            'куртка', 'пуховик', 'пальто', 'ветровка', 'бомбер', 
            'jacket', 'парка', 'косуха', 'зимняя куртка'
        ],
        'pants': [
            'штаны', 'джинсы', 'брюки', 'чиносы', 'карго', 
            'jeans', 'спортивные штаны'
        ],
        't-shirt': [
            'футболка', 'майка', 'лонгслив', 'поло', 
            't-shirt', 'футка', 'тенниска'
        ],
        'accessories': [
            'шапка', 'кепка', 'шарф', 'ремень', 'сумка', 
            'рюкзак', 'cap', 'перчатки', 'носки'
        ]
    }
    
    # Считаем количество совпадений для каждой категории
    matches = {category: 0 for category in categories}
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in text_lower:
                matches[category] += 1
    
    # Выбираем категорию с наибольшим количеством совпадений
    best_category = 'other'
    max_matches = 0
    
    for category, count in matches.items():
        if count > max_matches:
            max_matches = count
            best_category = category
    
    return best_category if max_matches > 0 else 'other'

def extract_brand(text: str) -> str:
    """
    Определяет бренд (дополнительная функция).
    """
    if not text:
        return ''
    
    text_lower = text.lower()
    
    brands = {
        'nike': ['nike', 'найк', 'air force', 'air max', 'джордан'],
        'adidas': ['adidas', 'адидас', 'yeezy', 'адик'],
        'converse': ['converse', 'конверс', 'chuck taylor'],
        'new balance': ['new balance', 'нью баланс', 'nb'],
        'gucci': ['gucci', 'гучи'],
        'balenciaga': ['balenciaga', 'баленсиага'],
        'off-white': ['off-white', 'офф вайт', 'offwhite'],
        'the north face': ['the north face', 'north face', 'tnf'],
        'levis': ['levis', 'левис', 'levi\'s', 'ливайс'],
    }
    
    for brand, keywords in brands.items():
        for keyword in keywords:
            if keyword in text_lower:
                return brand
    
    return ''

# ===== ГЛАВНАЯ ФУНКЦИЯ ОБРАБОТКИ =====

async def process_all_posts():
    """
    Обрабатывает все необработанные посты в базе данных.
    Запускать после того, как Влад нальет данные.
    """
    print("🔄 [ml_logic] Начинаю обработку постов...")
    
    try:
        # Получаем необработанные посты через функцию Леонида
        unprocessed = await get_unprocessed_posts()
    except Exception as e:
        print(f"❌ [ml_logic] Ошибка при получении постов: {e}")
        print("   Проверь:")
        print("   - Есть ли файл bot/database.py")
        print("   - Создана ли база данных (запусти сначала бота)")
        print(f"   - Путь к корню проекта: {root_dir}")
        return
    
    if not unprocessed:
        print("✅ [ml_logic] Нет необработанных постов!")
        return
    
    print(f"📊 [ml_logic] Найдено {len(unprocessed)} постов для обработки")
    
    # Статистика
    stats = {
        'total': len(unprocessed),
        'with_price': 0,
        'by_category': {}
    }
    
    processed = 0
    for post_id, raw_text in unprocessed:
        try:
            # Твоя магия обработки
            price = extract_price(raw_text)
            category = detect_category(raw_text)
            
            # Сохраняем результат через функцию Леонида
            await update_post_data(post_id, price, category)
            
            # Собираем статистику
            if price > 0:
                stats['with_price'] += 1
            
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
            
        except Exception as e:
            print(f"❌ [ml_logic] Ошибка при обработке поста {post_id}: {e}")
        
        processed += 1
        if processed % 10 == 0:
            print(f"⏳ [ml_logic] Обработано {processed}/{len(unprocessed)}...")
    
    # Выводим статистику
    print("\n" + "="*50)
    print("📊 [ml_logic] ОТЧЕТ ОБ ОБРАБОТКЕ")
    print("="*50)
    print(f"✅ Всего обработано: {stats['total']} постов")
    print(f"💰 Найдена цена: {stats['with_price']} постов ({stats['with_price']/stats['total']*100:.1f}%)")
    
    if stats['by_category']:
        print("\n📦 Распределение по категориям:")
        for cat, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count} ({count/stats['total']*100:.1f}%)")
    print("="*50)

# ===== ТЕСТОВАЯ ФУНКЦИЯ =====

async def test_on_samples():
    """Тестирует функции на примерах текстов."""
    
    test_samples = [
        {
            'text': "🔥 Nike Air Force 1 Low\nРазмеры: 41-45\nЦена: 8900₽\nНовые, оригинал",
            'expected_price': 8900,
            'expected_category': 'shoes'
        },
        {
            'text': "🧥 Зимний пуховик The North Face\nЦена: 15000 рублей\nРазмер M\nСамовывоз",
            'expected_price': 15000,
            'expected_category': 'outerwear'
        },
        {
            'text': "👕 Футболка Off-White\nНовая, с бирками\n1500₽",
            'expected_price': 1500,
            'expected_category': 't-shirt'
        },
        {
            'text': "📦 Adidas Yeezy Boost 350\nРазмер 43\nЦена: 18000 руб.",
            'expected_price': 18000,
            'expected_category': 'shoes'
        },
        {
            'text': "🛍 Джинсы Levi's 511\nБ/у, состояние отличное\n800 рублей",
            'expected_price': 800,
            'expected_category': 'pants'
        },
        {
            'text': "Шапка вязаная\nНовая\n500 руб",
            'expected_price': 500,
            'expected_category': 'accessories'
        }
    ]
    
    print("\n🧪 [ml_logic] ТЕСТИРОВАНИЕ ФУНКЦИЙ")
    print("="*60)
    
    success = 0
    for i, sample in enumerate(test_samples, 1):
        text = sample['text']
        expected_price = sample['expected_price']
        expected_category = sample['expected_category']
        
        price = extract_price(text)
        category = detect_category(text)
        
        price_ok = price == expected_price
        category_ok = category == expected_category
        
        print(f"\n{i}. Текст: {text[:50]}...")
        print(f"   Цена: {price} руб. (ожидалось: {expected_price}) {'✅' if price_ok else '❌'}")
        print(f"   Категория: {category} (ожидалось: {expected_category}) {'✅' if category_ok else '❌'}")
        
        if price_ok and category_ok:
            success += 1
    
    print("\n" + "="*60)
    print(f"✅ Тестов пройдено: {success}/{len(test_samples)}")
    print("="*60)

# ===== ТОЧКА ВХОДА =====

if __name__ == "__main__":
    import platform
    
    print(f"🐍 Python: {platform.python_version()}")
    print(f"📁 Папка проекта: {root_dir}")
    print(f"📁 Твоя папка: {Path(__file__).parent}")
    
    asyncio.run(test_on_samples())
    
    print("\n" + "="*60)
    
    # Потом обрабатываем реальные посты
    asyncio.run(process_all_posts())
