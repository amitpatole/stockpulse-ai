```python
from typing import Any
import os
from dotenv import load_dotenv

load_dotenv()

DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_URL = os.getenv("DB_URL", "sqlite:///tickerpulse.db")

def get_db_url() -> str:
    return DB_URL

def get_db_type() -> str:
    return DB_TYPE
```

--- FILE: backend/database.py ---
```python
from typing import Any, AsyncContextManager, AsyncGenerator, Optional
from contextlib import asynccontextmanager
import sqlite3
import aiopg

from .config import get_db_url, get_db_type

class Database:
    def __init__(self, db_url: str, db_type: str):
        self.db_url = db_url
        self.db_type = db_type

    async def connect(self) -> AsyncContextManager[sqlite3.Connection]:
        if self.db_type == "sqlite":
            conn = await sqlite3.connect(self.db_url, isolation_level=None, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn
        elif self.db_type == "postgresql":
            conn = await aiopg.create_pool(self.db_url)
            return conn
        else:
            raise ValueError(f"Unsupported database type: {self.db_type}")

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

--- FILE: backend/migrations.py ---
```python
from typing import Any
import os
from alembic.config import Config
from alembic import command

from .config import get_db_url

def migrate_database() -> None:
    db_url = get_db_url()
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    command.upgrade(alembic_cfg, "head")
```