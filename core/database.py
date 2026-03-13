import aiosqlite

DB_PATH = "data/fashion_bot.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_channel TEXT,
                raw_text TEXT,
                image_url TEXT,
                price INTEGER DEFAULT 0,
                category TEXT DEFAULT 'uncategorized',
                is_processed BOOLEAN DEFAULT 0
            )
        ''')
        await db.commit()

# Crawler
async def add_raw_post(channel: str, text: str, img: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO items (source_channel, raw_text, image_url) VALUES (?, ?, ?)",
            (channel, text, img)
        )
        await db.commit()
    print(f"Запись сохранена: {channel}")

# ML/Logic
async def get_unprocessed_posts():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT id, raw_text FROM items WHERE is_processed = 0") as cursor:
            return await cursor.fetchall()

async def update_post_data(post_id: int, price: int, category: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE items SET price = ?, category = ?, is_processed = 1 WHERE id = ?",
            (price, category, post_id)
        )
        await db.commit()

# Bot
async def search_items(search_query: str = None):
    # Все айтемы из базы
    query = "SELECT source_channel, raw_text, image_url, price FROM items ORDER BY id DESC"

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(query) as cursor:
            all_items = await cursor.fetchall()

            if not search_query:
                return all_items[:10]  # Если запроса нет, то 10 последних

            # Фильтруем на Python
            filtered = []
            search_query = search_query.lower().strip()

            for item in all_items:
                # item[1] — raw_text
                if search_query in item[1].lower():
                    filtered.append(item)

            print(f"DEBUG: Python нашел {len(filtered)} совпадений для '{search_query}'")
            return filtered