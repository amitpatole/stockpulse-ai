```python
"""
TickerPulse AI v3.0 - Central Configuration
All settings are driven by environment variables with sensible defaults.
"""

import os
import sys
from pathlib import Path


class Config:
    """Application configuration with environment variable overrides."""

    # -------------------------------------------------------------------------
    # Base paths
    # -------------------------------------------------------------------------
    if getattr(sys, 'frozen', False):
        # PyInstaller bundle: resolve from executable location
        BASE_DIR = Path(sys.executable).parent.parent
    else:
        BASE_DIR = Path(__file__).parent.parent  # tickerpulse-ai/

    # -------------------------------------------------------------------------
    # Database configuration
    # -------------------------------------------------------------------------
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite').lower()  # 'sqlite' or 'postgres'
    DB_PATH = os.getenv('DB_PATH', str(BASE_DIR / 'stock_news.db'))
    # DATABASE_URL: PostgreSQL connection string, required when DB_TYPE='postgres'
    # Format: postgresql://username:password@hostname:port/database_name
    # Only used if DB_TYPE='postgres'; SQLite uses DB_PATH instead
    DATABASE_URL = os.getenv(
        'DATABASE_URL',
        'postgresql://user:password@localhost:5432/tickerpulse'
    )
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 10))

    # -------------------------------------------------------------------------
    # Flask
    # -------------------------------------------------------------------------
    SECRET_KEY = os.getenv('SECRET_KEY', 'tickerpulse-dev-key-change-in-prod')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    CORS_ORIGINS = os.getenv(
        'CORS_ORIGINS',
        'http://localhost:3000,http://localhost:5000'
    ).split(',')

    # -------------------------------------------------------------------------
    # Market hours (24h format, timezone-aware)
    # -------------------------------------------------------------------------
    MARKET_TIMEZONE = os.getenv('MARKET_TIMEZONE', 'US/Eastern')

    # US market hours
    US_MARKET_OPEN = '09:30'
    US_MARKET_CLOSE = '16:00'

    # India market hours (IST / Asia/Kolkata)
    INDIA_MARKET_OPEN = '09:15'
    INDIA_MARKET_CLOSE = '15:30'
    INDIA_MARKET_TIMEZONE = 'Asia/Kolkata'

    # -------------------------------------------------------------------------
    # Monitoring / Scheduler
    # -------------------------------------------------------------------------
    CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 300))  # seconds (5 min)

    SCHEDULER_API_ENABLED = False  # Disabled -- we use our own scheduler_routes blueprint
    SCHEDULER_API_PREFIX = '/api/scheduler'
```