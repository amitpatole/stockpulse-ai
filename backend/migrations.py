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

def create_health_table() -> None:
    db_url = get_db_url()
    with app.app_context():
        db.engine.execute("""
            CREATE TABLE IF NOT EXISTS health_status (
                id INTEGER PRIMARY KEY,
                status TEXT NOT NULL,
                latency_ms REAL,
                error_rate REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
```