"""
Улучшенный модуль машинной логики для fashion-бота.
С поддержкой нечёткого поиска, синонимов категорий и умным исправлением опечаток.
"""

import sys
import re
from pathlib import Path
from fuzzywuzzy import fuzz, process

root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

try:
    from bot.database import get_unprocessed_posts, update_post_data
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# ===== НОРМАЛИЗОВАННЫЕ КАТЕГОРИИ С СИНОНИМАМИ =====
# Ключ – нормализованное имя категории, значение – список ключевых слов (включая синонимы на разных языках)
CATEGORY_SYNONYMS = {
    'shoes': [
        'кеды', 'кроссовки', 'обувь', 'ботинки', 'туфли', 'sneakers',
        'nike', 'adidas', 'найк', 'адидас', 'converse', 'new balance',
        'timberland', 'доктор мартинс', 'dr martens', 'сандалии', 'сандали',
        'каблуки', 'лодочки', 'балетки', 'мокасины', 'лоферы', 'слипоны'
    ],
    'hoodie': [
        'худи', 'толстовка', 'свитшот', 'кофта', 'олимпийка', 'hoodie',
        'свитер', 'байка', 'свитшот', 'лонгслив'
    ],
    'outerwear': [
        'куртка', 'пуховик', 'пальто', 'ветровка', 'бомбер', 'jacket',
        'плащ', 'тренч', 'косуха', 'парка', 'аляска', 'зимняя куртка',
        'кожанка', 'дождевик', 'анорак'
    ],
    'pants': [
        'штаны', 'джинсы', 'брюки', 'чиносы', 'карго', 'jeans',
        'спортивные штаны', 'треники', 'лосины', 'леггинсы', 'шорты',
        'бермуды', 'брюки-клеш', 'слаксы'
    ],
    't-shirt': [
        'футболка', 'майка', 'лонгслив', 'поло', 't-shirt', 'футка',
        'тенниска', 'футболочка', 'футболка', 'топ', 'боди'
    ],
    'accessories': [
        'шапка', 'кепка', 'шарф', 'ремень', 'сумка', 'рюкзак',
        'бейсболка', 'панама', 'перчатки', 'носки', 'бандана',
        'очки', 'солнцезащитные очки', 'часы', 'браслет', 'цепочка'
    ]
}

# Плоский список всех ключевых слов для быстрого нечёткого поиска
ALL_KEYWORDS = []
KEYWORD_TO_CATEGORY = {}
for category, keywords in CATEGORY_SYNONYMS.items():
    for kw in keywords:
        ALL_KEYWORDS.append(kw)
        KEYWORD_TO_CATEGORY[kw] = category

# Стоп-слова (игнорируются при анализе)
STOP_WORDS = {
    'продам', 'продажа', 'купить', 'цена', 'руб', '₽', 'рублей',
    'новый', 'новое', 'новая', 'новые', 'бу', 'б/у', 'used',
    'размер', 'размеры', 's', 'm', 'l', 'xl', 'xxl',
    'доставка', 'самовывоз', 'торг', 'уместен', 'оригинал',
    'качество', 'бренд', 'состояние', 'отличное', 'хорошее',
    'связь', 'наличие', 'тег', 'тел', 'viber', 'whatsapp', 'inst', 'instagram'
}

# Порог уверенности для нечёткого сравнения (0-100)
FUZZY_THRESHOLD = 70

def clean_text(text: str) -> str:
    """Очищает текст от мусора, эмодзи, ссылок и лишних символов."""
    if not text:
        return ""

    text = re.sub(r'@\w+', '', text)          # упоминания
    text = re.sub(r'https?://\S+', '', text) # ссылки
    text = re.sub(r't\.me/\S+', '', text)    # ссылки telegram
    text = re.sub(r'#\w+', '', text)         # хештеги

    # удаляем эмодзи
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"
                               u"\U0001F300-\U0001F5FF"
                               u"\U0001F680-\U0001F6FF"
                               u"\U0001F1E0-\U0001F1FF"
                               "]+", flags=re.UNICODE)
    text = emoji_pattern.sub('', text)

    # заменяем множественные пробелы
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_price(text: str) -> int:
    """Извлекает цену из текста, учитывая разные форматы."""
    if not text:
        return 0

    text = text.lower()

    # регулярки для поиска цен с валютой и без
    patterns = [
        r'(\d+)[\s]?(?:₽|руб|рублей|рубля|р\.?|руб\.)',
        r'(\d+)[\s]?(?:usd|\$|dollars?)',
        r'(\d+)[\s]?(?:eur|евро|€)',
        r'(?:₽|руб|рублей|рубля|р\.?)[\s]*(\d+)',
        r'(?:\$|usd)[\s]*(\d+)',
        r'(?:€|eur|евро)[\s]*(\d+)',
        r'цена[:\s]*(\d+)',
        r'стоит[:\s]*(\d+)',
        r'за\s*(\d+)',
        r'\b(\d{3,7})\b',   # обычное число от 100 до 9.999.999
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                for group in match:
                    if group and group.isdigit():
                        price = int(group)
                        if 100 <= price <= 10000000:
                            return price
            elif match and match.isdigit():
                price = int(match)
                if 100 <= price <= 10000000:
                    return price

    # если не нашли – берём самое большое число среди всех чисел >100
    numbers = re.findall(r'\b(\d+)\b', text)
    if numbers:
        valid_prices = [int(n) for n in numbers if int(n) > 100 and int(n) < 10000000]
        if valid_prices:
            return max(valid_prices)

    return 0

def find_best_category_for_word(word: str) -> tuple:
    """
    Возвращает (категория, уверенность) для одного слова.
    Использует нечёткое сравнение со всеми ключевыми словами всех категорий.
    """
    if len(word) < 2 or word in STOP_WORDS:
        return None, 0

    # ищем лучшее совпадение среди всех ключевых слов
    best = process.extractOne(word, ALL_KEYWORDS, scorer=fuzz.token_set_ratio)
    if not best:
        return None, 0

    matched_keyword, confidence = best
    if confidence < FUZZY_THRESHOLD:
        return None, 0

    category = KEYWORD_TO_CATEGORY[matched_keyword]
    return category, confidence

def detect_category(text: str) -> str:
    """Определяет категорию, агрегируя оценки по всем словам."""
    if not text:
        return 'other'

    cleaned = clean_text(text)
    words = re.findall(r'\b[a-zA-Zа-яА-Я0-9]+\b', cleaned.lower())

    # считаем очки для каждой категории
    category_scores = {cat: 0 for cat in CATEGORY_SYNONYMS}

    for word in words:
        if word in STOP_WORDS:
            continue

        # точное совпадение с любым ключевым словом
        if word in KEYWORD_TO_CATEGORY:
            cat = KEYWORD_TO_CATEGORY[word]
            category_scores[cat] += 100
            continue

        # нечёткое совпадение
        best_cat, confidence = find_best_category_for_word(word)
        if best_cat:
            category_scores[best_cat] += confidence

    # выбираем категорию с наибольшим счётом
    best_category = 'other'
    max_score = 30  # минимальный порог, чтобы не срабатывало от случайных совпадений

    for cat, score in category_scores.items():
        if score > max_score:
            max_score = score
            best_category = cat

    return best_category

def process_text(text: str):
    """Обрабатывает один текст и возвращает (цена, категория)."""
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
