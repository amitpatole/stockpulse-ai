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