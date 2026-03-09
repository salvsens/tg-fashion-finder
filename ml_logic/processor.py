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
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

print(f"📁 Корневая папка проекта: {root_dir}")
print(f"📁 Текущая папка: {Path(__file__).parent}")

try:
    from bot.database import get_unprocessed_posts, update_post_data
    print("✅ Модуль database успешно импортирован")
except Exception as e:
    print(f"❌ Ошибка импорта database: {e}")
    print("   Проверь структуру папок:")
    print("   - Есть ли папка bot/")
    print("   - Есть ли файл bot/database.py")
    print("   - Есть ли файл bot/__init__.py")
    sys.exit(1)

# ===== ТВОИ ФУНКЦИИ ОБРАБОТКИ =====

def extract_price(text: str) -> int:
    """Извлекает цену из текста поста."""
    if not text:
        return 0
    
    text = text.lower()
    print(f"   🔍 Ищем цену в: {text[:50]}...")
    
    patterns = [
        r'(\d+)[\s]?(?:₽|руб|рублей|рубля|р\.?)',
        r'(?:₽|руб|рублей|рубля|р\.?)[\s]*(\d+)',
        r'цена[:\s]*(\d+)',
        r'(\d{3,6})\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            for group in match.groups():
                if group and group.isdigit():
                    price = int(group)
                    if 10 < price < 1000000:
                        print(f"   ✅ Найдена цена: {price}")
                        return price
    
    print(f"   ❌ Цена не найдена")
    return 0

def detect_category(text: str) -> str:
    """Определяет категорию одежды по ключевым словам."""
    if not text:
        return 'other'
    
    text_lower = text.lower()
    print(f"   🔍 Ищем категорию в: {text[:50]}...")
    
    categories = {
        'shoes': ['кеды', 'кроссовки', 'обувь', 'ботинки', 'туфли', 'sneakers', 'nike', 'adidas'],
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
                print(f"   📌 Найдено ключевое слово '{keyword}' -> {category}")
    
    best_category = 'other'
    max_matches = 0
    
    for category, count in matches.items():
        if count > max_matches:
            max_matches = count
            best_category = category
    
    if max_matches > 0:
        print(f"   ✅ Определена категория: {best_category}")
    else:
        print(f"   ❌ Категория не определена, ставлю 'other'")
    
    return best_category if max_matches > 0 else 'other'

# ===== ТЕСТОВАЯ ФУНКЦИЯ =====

async def test_on_samples():
    """Тестирует функции на примерах."""
    
    test_samples = [
        "🔥 Nike Air Force 1 Low\nЦена: 8900₽",
        "🧥 Пуховик The North Face\n15000 рублей",
        "👕 Футболка Off-White\n1500₽",
        "📦 Adidas Yeezy\nЦена: 18000 руб.",
        "🛍 Джинсы Levi's\n800 рублей",
        "Шапка вязаная\n500 руб"
    ]
    
    print("\n" + "="*60)
    print("🧪 ТЕСТИРОВАНИЕ ФУНКЦИЙ НА ПРИМЕРАХ")
    print("="*60)
    
    for i, text in enumerate(test_samples, 1):
        print(f"\n{i}. Тестовый текст: {text}")
        price = extract_price(text)
        category = detect_category(text)
        print(f"   ИТОГ: цена={price}, категория={category}")
    
    print("\n" + "="*60)
    print("✅ Тестирование завершено")
    print("="*60)

# ===== ПРОВЕРКА БАЗЫ ДАННЫХ =====

async def check_database():
    """Проверяет, есть ли что-то в базе данных."""
    print("\n" + "="*60)
    print("🔍 ПРОВЕРКА БАЗЫ ДАННЫХ")
    print("="*60)
    
    # Проверяем существование файла базы данных
    db_path = root_dir / "bot" / "data" / "fashion_bot.db"
    print(f"📁 Путь к БД: {db_path}")
    
    if not db_path.exists():
        print("❌ Файл базы данных не найден!")
        print("   Возможные причины:")
        print("   - База еще не создана (нужно запустить бота Леонида)")
        print("   - Неправильный путь к БД")
        return False
    
    print(f"✅ Файл БД найден, размер: {db_path.stat().st_size} байт")
    
    # Проверяем, есть ли необработанные посты
    try:
        unprocessed = await get_unprocessed_posts()
        print(f"📊 Найдено необработанных постов: {len(unprocessed)}")
        
        if len(unprocessed) == 0:
            print("\n💡 ПОЧЕМУ НЕТ ПОСТОВ:")
            print("   1. Влад еще не запустил парсер")
            print("   2. В переменной CHANNEL_IDS нет каналов")
            print("   3. База пустая (нужно подождать данных от Влада)")
            print("\n💡 ЧТО ДЕЛАТЬ:")
            print("   - Спроси у Влада, запустил ли он парсер")
            print("   - Попроси Леонида добавить тестовые данные")
            print("   - Или подожди, пока ребята настроят свои части")
        
        return unprocessed
    except Exception as e:
        print(f"❌ Ошибка при запросе к БД: {e}")
        return False

# ===== ГЛАВНАЯ ФУНКЦИЯ =====

async def main():
    """Главная функция."""
    print("\n" + "="*60)
    print("🚀 ЗАПУСК ML LOGIC PROCESSOR")
    print("="*60)
    
    # Сначала тестируем функции
    await test_on_samples()
    
    # Проверяем базу данных
    unprocessed = await check_database()
    
    if unprocessed:
        print(f"\n📊 Начинаю обработку {len(unprocessed)} постов...")
        
        processed = 0
        success = 0
        
        for post_id, raw_text in unprocessed:
            print(f"\n--- Обработка поста ID: {post_id} ---")
            print(f"Текст: {raw_text[:100]}..." if len(raw_text) > 100 else f"Текст: {raw_text}")
            
            try:
                price = extract_price(raw_text)
                category = detect_category(raw_text)
                
                await update_post_data(post_id, price, category)
                print(f"✅ Пост {post_id} сохранен: price={price}, category={category}")
                success += 1
                
            except Exception as e:
                print(f"❌ Ошибка при обработке поста {post_id}: {e}")
            
            processed += 1
        
        print("\n" + "="*60)
        print(f"📊 ИТОГИ ОБРАБОТКИ")
        print("="*60)
        print(f"✅ Обработано постов: {processed}")
        print(f"✅ Успешно сохранено: {success}")
        print("="*60)
    else:
        print("\n⏳ Нет данных для обработки. Ждем, пока Влад нальет посты в базу.")
    
    print("\n✅ Работа процессора завершена")

# ===== ТОЧКА ВХОДА =====

if __name__ == "__main__":
    asyncio.run(main())
