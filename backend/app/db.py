from typing import Any
from contextlib import asynccontextmanager
from sqlite3 import Error
from config import DATABASE_PATH

@asynccontextmanager
async def get_db_connection():
    conn = await sqlite3.connect(DATABASE_PATH, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        await conn.close()

async def init_db() -> None:
    async with get_db_connection() as conn:
        cursor = await conn.cursor()
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_sentiment (
                id INTEGER PRIMARY KEY,
                stock_symbol TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                sentiment_score REAL
            )
        ''')
        await cursor.execute('''
            CREATE TABLE IF NOT EXISTS trending_mentions (
                id INTEGER PRIMARY KEY,
                stock_symbol TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                mention_count INTEGER
            )
        ''')
        await conn.commit()