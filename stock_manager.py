#!/usr/bin/env python3
"""
Stock Manager - Handles dynamic stock list management
"""

import sqlite3
import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

DB_PATH = 'stock_news.db'


def init_stocks_table():
    """Initialize stocks table in database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create stocks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        )
    ''')

    # Add default stocks if table is empty
    cursor.execute('SELECT COUNT(*) FROM stocks')
    if cursor.fetchone()[0] == 0:
        default_stocks = [
            ('TSLA', 'Tesla Inc'),
            ('AAPL', 'Apple Inc'),
            ('MSFT', 'Microsoft Corporation'),
            ('NVDA', 'NVIDIA Corporation'),
            ('GOOGL', 'Alphabet Inc'),
            ('AMZN', 'Amazon.com Inc'),
            ('META', 'Meta Platforms Inc'),
            ('NFLX', 'Netflix Inc'),
            ('AMD', 'Advanced Micro Devices'),
            ('COIN', 'Coinbase Global Inc')
        ]

        cursor.executemany(
            'INSERT INTO stocks (ticker, name) VALUES (?, ?)',
            default_stocks
        )
        logger.info(f"Added {len(default_stocks)} default stocks")

    conn.commit()
    conn.close()


def get_active_stocks() -> List[str]:
    """Get list of active stock tickers"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT ticker FROM stocks WHERE active = 1 ORDER BY ticker')
    stocks = [row['ticker'] for row in cursor.fetchall()]

    conn.close()
    return stocks


def get_all_stocks() -> List[Dict]:
    """Get all stocks with details"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM stocks ORDER BY ticker')
    stocks = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return stocks


def add_stock(ticker: str, name: str) -> bool:
    """Add a new stock to monitor"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        ticker = ticker.upper()
        cursor.execute(
            'INSERT OR REPLACE INTO stocks (ticker, name, active) VALUES (?, ?, 1)',
            (ticker, name)
        )

        conn.commit()
        conn.close()
        logger.info(f"Added stock: {ticker} - {name}")
        return True
    except Exception as e:
        logger.error(f"Error adding stock {ticker}: {e}")
        return False


def remove_stock(ticker: str) -> bool:
    """Remove a stock from monitoring (soft delete)"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        ticker = ticker.upper()
        cursor.execute('UPDATE stocks SET active = 0 WHERE ticker = ?', (ticker,))

        conn.commit()
        conn.close()
        logger.info(f"Removed stock: {ticker}")
        return True
    except Exception as e:
        logger.error(f"Error removing stock {ticker}: {e}")
        return False


def search_stock_ticker(query: str) -> List[Dict]:
    """
    Search for stock tickers using Yahoo Finance
    Returns list of matching stocks with ticker and name
    """
    try:
        # Use Yahoo Finance search
        url = f"https://query2.finance.yahoo.com/v1/finance/search"
        params = {
            'q': query,
            'quotesCount': 10,
            'newsCount': 0,
            'enableFuzzyQuery': False,
            'quotesQueryId': 'tss_match_phrase_query'
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        response = requests.get(url, params=params, headers=headers, timeout=5)

        if response.status_code == 200:
            data = response.json()
            results = []

            for quote in data.get('quotes', []):
                # Only include stocks (not ETFs, mutual funds, etc unless explicitly stocks)
                if quote.get('quoteType') in ['EQUITY', 'ETF']:
                    results.append({
                        'ticker': quote.get('symbol', ''),
                        'name': quote.get('longname') or quote.get('shortname', ''),
                        'exchange': quote.get('exchange', ''),
                        'type': quote.get('quoteType', '')
                    })

            return results[:10]  # Return top 10 matches

    except Exception as e:
        logger.error(f"Error searching for ticker '{query}': {e}")

    return []


if __name__ == '__main__':
    # Initialize table
    init_stocks_table()

    # Test search
    results = search_stock_ticker('tesla')
    print(f"Search results for 'tesla':")
    for r in results:
        print(f"  {r['ticker']}: {r['name']}")
