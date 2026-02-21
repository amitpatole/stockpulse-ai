#!/usr/bin/env python3
"""
Stock Manager - Handles dynamic stock list management
"""

import sqlite3
import requests
import logging
from typing import List, Dict, Optional

from backend.config import Config

logger = logging.getLogger(__name__)


def init_stocks_table():
    """Initialize stocks table in database"""
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()

    # Create stocks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            market TEXT DEFAULT 'US',
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        )
    ''')

    # Add market column to existing tables (migration)
    try:
        cursor.execute('ALTER TABLE stocks ADD COLUMN market TEXT DEFAULT "US"')
    except sqlite3.OperationalError:
        # Column already exists
        pass

    # Add default stocks if table is empty
    cursor.execute('SELECT COUNT(*) FROM stocks')
    if cursor.fetchone()[0] == 0:
        default_stocks = [
            # US Stocks
            ('TSLA', 'Tesla Inc', 'US'),
            ('AAPL', 'Apple Inc', 'US'),
            ('MSFT', 'Microsoft Corporation', 'US'),
            ('NVDA', 'NVIDIA Corporation', 'US'),
            ('GOOGL', 'Alphabet Inc', 'US'),
            ('AMZN', 'Amazon.com Inc', 'US'),
            ('META', 'Meta Platforms Inc', 'US'),
            ('NFLX', 'Netflix Inc', 'US'),
            ('AMD', 'Advanced Micro Devices', 'US'),
            ('COIN', 'Coinbase Global Inc', 'US'),
            # Indian Stocks - NSE (National Stock Exchange)
            ('RELIANCE.NS', 'Reliance Industries Ltd (NSE)', 'India'),
            ('TCS.NS', 'Tata Consultancy Services (NSE)', 'India'),
            ('HDFCBANK.NS', 'HDFC Bank Ltd (NSE)', 'India'),
            ('INFY.NS', 'Infosys Ltd (NSE)', 'India'),
            ('ICICIBANK.NS', 'ICICI Bank Ltd (NSE)', 'India'),
            # Indian Stocks - BSE (Bombay Stock Exchange)
            ('RELIANCE.BO', 'Reliance Industries Ltd (BSE)', 'India'),
            ('TCS.BO', 'Tata Consultancy Services (BSE)', 'India'),
            ('HDFCBANK.BO', 'HDFC Bank Ltd (BSE)', 'India'),
            ('INFY.BO', 'Infosys Ltd (BSE)', 'India'),
            ('ICICIBANK.BO', 'ICICI Bank Ltd (BSE)', 'India')
        ]

        cursor.executemany(
            'INSERT INTO stocks (ticker, name, market) VALUES (?, ?, ?)',
            default_stocks
        )
        logger.info(f"Added {len(default_stocks)} default stocks (US + India NSE/BSE)")

    conn.commit()
    conn.close()


def get_active_stocks() -> List[str]:
    """Get list of active stock tickers"""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT ticker FROM stocks WHERE active = 1 ORDER BY ticker')
    stocks = [row['ticker'] for row in cursor.fetchall()]

    conn.close()
    return stocks


def get_all_stocks() -> List[Dict]:
    """Get all stocks with details"""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM stocks ORDER BY ticker')
    stocks = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return stocks


def add_stock(ticker: str, name: str, market: str = 'US') -> bool:
    """Add a new stock to monitor"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        ticker = ticker.upper()
        # Auto-detect market based on ticker suffix
        if '.NS' in ticker or '.BO' in ticker:
            market = 'India'

        cursor.execute(
            'INSERT OR REPLACE INTO stocks (ticker, name, market, active) VALUES (?, ?, ?, 1)',
            (ticker, name, market)
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
        conn = sqlite3.connect(Config.DB_PATH)
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
    query = query.strip()
    if not query:
        return []
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
