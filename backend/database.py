```python
from typing import Any, AsyncContextManager, AsyncGenerator, Optional
from contextlib import asynccontextmanager
import sqlite3
import logging
from backend.config import get_db_url

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_url: str):
        self.db_url = db_url

    async def connect(self) -> AsyncContextManager[sqlite3.Connection]:
        conn = await sqlite3.connect(self.db_url, isolation_level=None, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    async def execute(self, query: str, params: Optional[tuple] = None) -> AsyncGenerator[sqlite3.Row, None]:
        async with self.connect() as conn:
            cursor = await conn.cursor()
            await cursor.execute(query, params)
            yield cursor
            await cursor.close()

    async def fetch_all(self, query: str, params: Optional[tuple] = None) -> list[sqlite3.Row]:
        async for row in self.execute(query, params):
            yield row

    async def fetch_one(self, query: str, params: Optional[tuple] = None) -> Optional[sqlite3.Row]:
        async for row in self.execute(query, params):
            return row
        return None

    async def fetch_val(self, query: str, params: Optional[tuple] = None) -> Optional[Any]:
        row = await self.fetch_one(query, params)
        return row[0] if row else None
```