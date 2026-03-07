```python
from typing import Any
import os
from dotenv import load_dotenv

load_dotenv()

DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_URL = os.getenv("DB_URL", "sqlite:///tickerpulse.db")

CRYPTO_API_URL = os.getenv("CRYPTO_API_URL", "https://api.coingecko.com/api/v3")

def get_db_url() -> str:
    return DB_URL

def get_db_type() -> str:
    return DB_TYPE

def get_crypto_api_url() -> str:
    return CRYPTO_API_URL
```