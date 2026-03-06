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
    DB_PATH = os.getenv('DB_PATH', str(BASE_DIR / 'stock_news.db'))
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')

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

    # -------------------------------------------------------------------------
    # AI Providers (can also be configured via the Settings UI)
    # -------------------------------------------------------------------------
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    GOOGLE_AI_KEY = os.getenv('GOOGLE_AI_KEY', '')
    XAI_API_KEY = os.getenv('XAI_API_KEY', '')

    # Default AI model per provider (used when no model is specified in DB)
    DEFAULT_MODELS = {
        'anthropic': 'claude-sonnet-4-20250514',
        'openai': 'gpt-4o',
        'google': 'gemini-2.0-flash',
        'xai': 'grok-3',
    }

    # -------------------------------------------------------------------------
    # Database configuration
    # -------------------------------------------------------------------------
    if DB_TYPE == 'postgresql':
        SQLALCHEMY_DATABASE_URI = os.getenv(
            'DATABASE_URL',
            'postgresql://user:password@localhost:5432/tickerpulse'
        )
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DB_PATH
```