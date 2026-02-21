#!/usr/bin/env python3
"""
Settings Manager
Handles application settings including AI provider API keys
"""

import sqlite3
import logging
import threading
from typing import Dict, Optional

from backend.config import Config

logger = logging.getLogger(__name__)

# Module-level lock serialises all multi-step write operations so that
# concurrent requests cannot interleave the deactivate-all → check-exists →
# insert/update sequence and leave 0 or 2+ active providers in the database.
_lock = threading.RLock()


def init_settings_table():
    """Initialize settings table in database"""
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()

    # Create settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create AI providers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_providers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            provider_name TEXT NOT NULL,
            api_key TEXT NOT NULL,
            model TEXT,
            is_active INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    logger.info("Settings tables initialized")


def get_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get a setting value"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()

        conn.close()

        return result[0] if result else default
    except Exception as e:
        logger.error(f"Error getting setting {key}: {e}")
        return default


def set_setting(key: str, value: str):
    """Set a setting value"""
    with _lock:
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, datetime('now'))
            ''', (key, value))

            conn.commit()
            conn.close()
            logger.info(f"Setting {key} updated")
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")


def get_active_ai_provider() -> Optional[Dict]:
    """Get the currently active AI provider"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM ai_providers
            WHERE is_active = 1
            ORDER BY updated_at DESC
            LIMIT 1
        ''')

        result = cursor.fetchone()
        conn.close()

        if result:
            return {
                'id': result['id'],
                'provider_name': result['provider_name'],
                'api_key': result['api_key'],
                'model': result['model']
            }
        return None
    except Exception as e:
        logger.error(f"Error getting active AI provider: {e}")
        return None


def get_all_ai_providers() -> list:
    """Get all configured AI providers"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT id, provider_name, model, is_active, created_at, updated_at
            FROM ai_providers
            ORDER BY updated_at DESC
        ''')

        results = cursor.fetchall()
        conn.close()

        return [{
            'id': row['id'],
            'provider_name': row['provider_name'],
            'model': row['model'],
            'is_active': row['is_active'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        } for row in results]
    except Exception as e:
        logger.error(f"Error getting AI providers: {e}")
        return []


def add_ai_provider(provider_name: str, api_key: str, model: Optional[str] = None, set_active: bool = True) -> bool:
    """Add or update an AI provider"""
    with _lock:
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            cursor = conn.cursor()

            # If setting as active, deactivate all others
            if set_active:
                cursor.execute('UPDATE ai_providers SET is_active = 0')

            # Check if provider already exists
            cursor.execute('''
                SELECT id FROM ai_providers
                WHERE provider_name = ?
            ''', (provider_name,))

            existing = cursor.fetchone()

            if existing:
                # Update existing
                cursor.execute('''
                    UPDATE ai_providers
                    SET api_key = ?, model = ?, is_active = ?, updated_at = datetime('now')
                    WHERE provider_name = ?
                ''', (api_key, model, 1 if set_active else 0, provider_name))
            else:
                # Insert new
                cursor.execute('''
                    INSERT INTO ai_providers (provider_name, api_key, model, is_active)
                    VALUES (?, ?, ?, ?)
                ''', (provider_name, api_key, model, 1 if set_active else 0))

            conn.commit()
            conn.close()
            logger.info(f"AI provider {provider_name} added/updated")
            return True
        except Exception as e:
            logger.error(f"Error adding AI provider: {e}")
            return False


def set_active_provider(provider_id: int) -> bool:
    """Set a provider as active"""
    with _lock:
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            cursor = conn.cursor()

            # Deactivate all
            cursor.execute('UPDATE ai_providers SET is_active = 0')

            # Activate selected
            cursor.execute('''
                UPDATE ai_providers
                SET is_active = 1, updated_at = datetime('now')
                WHERE id = ?
            ''', (provider_id,))

            conn.commit()
            conn.close()
            logger.info(f"Provider {provider_id} set as active")
            return True
        except Exception as e:
            logger.error(f"Error setting active provider: {e}")
            return False


def delete_ai_provider(provider_id: int) -> bool:
    """Delete an AI provider"""
    with _lock:
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM ai_providers WHERE id = ?', (provider_id,))

            conn.commit()
            conn.close()
            logger.info(f"Provider {provider_id} deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting provider: {e}")
            return False


def is_ai_enabled() -> bool:
    """Check if AI is enabled (has active provider)"""
    provider = get_active_ai_provider()
    return provider is not None


if __name__ == '__main__':
    # Initialize tables
    init_settings_table()
    print("Settings tables initialized")
