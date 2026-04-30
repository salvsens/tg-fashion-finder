"""
Улучшенный модуль машинной логики для fashion-бота.
С поддержкой NLTK (стемминг, токенизация, стоп-слова), нечёткого поиска и умным извлечением цены.
"""

import sys
import re
from pathlib import Path

from fuzzywuzzy import fuzz, process
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

# Инициализация NLTK
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("Загрузка компонентов NLTK...")
    nltk.download('punkt', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    nltk.download('stopwords', quiet=True)

root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

try:
    from bot.database import get_unprocessed_posts, update_post_data
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

# Инициализация стеммера для русского языка
stemmer = SnowballStemmer("russian")

# НОРМАЛИЗОВАННЫЕ КАТЕГОРИИ С СИНОНИМАМИ
CATEGORY_SYNONYMS = {
    'shoes': [
        'кеды', 'кроссовки', 'обувь', 'ботинки', 'туфли', 'sneakers',
        'nike', 'adidas', 'найк', 'адидас', 'converse', 'new balance',
        'timberland', 'доктор мартинс', 'dr martens', 'сандалии', 'сандали',
        'каблуки', 'лодочки', 'балетки', 'мокасины', 'лоферы', 'слипоны'
    ],
    'hoodie': [
        'худи', 'толстовка', 'свитшот', 'кофта', 'олимпийка', 'hoodie',
        'свитер', 'байка', 'лонгслив'
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
        'футболка', 'майка', 'поло', 't-shirt', 'футка',
        'тенниска', 'футболочка', 'топ', 'боди'
    ],
    'accessories': [
        'шапка', 'кепка', 'шарф', 'ремень', 'сумка', 'рюкзак',
        'бейсболка', 'панама', 'перчатки', 'носки', 'бандана',
        'очки', 'солнцезащитные очки', 'часы', 'браслет', 'цепочка'
    ]
}

# Плоские списки для поиска
ALL_KEYWORDS = []
KEYWORD_TO_CATEGORY = {}
STEMMED_KEYWORD_TO_CATEGORY = {}

for category, keywords in CATEGORY_SYNONYMS.items():
    for kw in keywords:
        ALL_KEYWORDS.append(kw)
        KEYWORD_TO_CATEGORY[kw] = category
        stemmed_kw = " ".join([stemmer.stem(w) for w in kw.split()])
        STEMMED_KEYWORD_TO_CATEGORY[stemmed_kw] = category

# Собственный стоп-слова
CUSTOM_STOP_WORDS = {
    'продам', 'продажа', 'купить', 'цена', 'руб', '₽', 'рублей',
    'новый', 'новое', 'новая', 'новые', 'бу', 'б/у', 'used',
    'размер', 'размеры', 's', 'm', 'l', 'xl', 'xxl',
    'доставка', 'самовывоз', 'торг', 'уместен', 'оригинал',
    'качество', 'бренд', 'состояние', 'отличное', 'хорошее',
    'связь', 'наличие', 'тег', 'тел', 'viber', 'whatsapp', 'inst', 'instagram'
}
NLTK_STOP_WORDS = set(stopwords.words('russian'))
COMBINED_STOP_WORDS = CUSTOM_STOP_WORDS.union(NLTK_STOP_WORDS)

# Порог уверенности для нечёткого сравнения (0-100)
FUZZY_THRESHOLD = 75

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

    # замена знаков препинания на пробелы
    text = re.sub(r'[^\w\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_price(text: str) -> int:
    """Извлекает цену из текста, учитывая разные форматы."""
    if not text:
        return 0

    text = text.lower()
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
        r'\b(\d{3,7})\b',
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

    numbers = re.findall(r'\b(\d+)\b', text)
    if numbers:
        valid_prices = [int(n) for n in numbers if 100 < int(n) < 10000000]
        if valid_prices:
            return max(valid_prices)

    return 0

def find_best_category_for_word(word: str) -> tuple:
    """
    Возвращает (категория, уверенность) для одного слова.
    Использует нечёткое сравнение со всеми оригинальными ключевыми словами.
    """
    if len(word) < 2:
        return None, 0

    best = process.extractOne(word, ALL_KEYWORDS, scorer=fuzz.token_set_ratio)
    if not best:
        return None, 0

    matched_keyword, confidence = best
    if confidence < FUZZY_THRESHOLD:
        return None, 0

    category = KEYWORD_TO_CATEGORY[matched_keyword]
    return category, confidence

def detect_category(text: str) -> str:
    """Определяет категорию, агрегируя оценки по всем словам (NLTK Tokenization + Stemming)."""
    if not text:
        return 'other'

    cleaned = clean_text(text).lower()

    # NLTK Токенизация
    words = word_tokenize(cleaned, language='russian')

    category_scores = {cat: 0 for cat in CATEGORY_SYNONYMS}

    for word in words:
        if not word.isalnum() or word in COMBINED_STOP_WORDS:
            continue

        # NLTK Стемминг
        stemmed_word = stemmer.stem(word)

        # 1. Проверка по стеммированной базе
        if stemmed_word in STEMMED_KEYWORD_TO_CATEGORY:
            cat = STEMMED_KEYWORD_TO_CATEGORY[stemmed_word]
            category_scores[cat] += 100
            continue

        # 2. Проверка точного вхождения оригинального слова
        if word in KEYWORD_TO_CATEGORY:
            cat = KEYWORD_TO_CATEGORY[word]
            category_scores[cat] += 90
            continue

        # 3. Нечёткое совпадение для опечаток (самое ресурсоемкое)
        best_cat, confidence = find_best_category_for_word(word)
        if best_cat:
            category_scores[best_cat] += confidence

    best_category = 'other'
    max_score = 40

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
        print("База данных недоступна. Проверьте импорты.")
        return

    unprocessed = await get_unprocessed_posts()
    if not unprocessed:
        return

    for post_id, raw_text in unprocessed:
        price = extract_price(raw_text)
        category = detect_category(raw_text)
        await update_post_data(post_id, price, category)
