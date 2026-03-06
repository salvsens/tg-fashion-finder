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
async def search_items(category: str = None, max_price: int = None):
    query = "SELECT source_channel, raw_text, image_url, price FROM items WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = ?"
        params.append(category)
    if max_price:
        query += " AND price <= ?"
        params.append(max_price)
        
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(query, params) as cursor:
            return await cursor.fetchall()