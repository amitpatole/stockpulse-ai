```python
#!/usr/bin/env python3
"""
Stock Manager - Handles dynamic stock list management with optimized queries.
Includes watchlist group management and stock organization.
"""

import sqlite3
import requests
import logging
from typing import List, Dict, Optional, Tuple

from backend.config import Config
from backend.database import db_session

logger = logging.getLogger(__name__)


def init_stocks_table():
    """Initialize stocks table in database"""
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()

    # Create watchlist_groups table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist_groups (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL UNIQUE,
            description     TEXT,
            color           TEXT DEFAULT '#6366f1',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create stocks table with group support
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stocks (
            ticker TEXT PRIMARY KEY,
            name TEXT,
            market TEXT DEFAULT 'US',
            group_id INTEGER REFERENCES watchlist_groups(id) ON DELETE SET NULL,
            sort_order INTEGER DEFAULT 0,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            active INTEGER DEFAULT 1
        )
    ''')

    # Create index
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_stocks_group_order ON stocks(group_id, sort_order)
    ''')

    # Add columns if missing (migration)
    try:
        cursor.execute('ALTER TABLE stocks ADD COLUMN group_id INTEGER REFERENCES watchlist_groups(id) ON DELETE SET NULL')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE stocks ADD COLUMN sort_order INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
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


def get_stocks_with_filter(
    market: Optional[str] = None,
    group_id: Optional[int] = None,
    limit: int = 20,
    offset: int = 0
) -> Tuple[List[sqlite3.Row], int]:
    """
    Get paginated active stocks with optional market and group filtering.

    Args:
        market: Optional market filter (e.g., 'US', 'India', None for all)
        group_id: Optional group filter (None for ungrouped only)
        limit: Rows per page (1-100, default 20)
        offset: Starting row offset

    Returns:
        Tuple of (stocks as Row objects, total_count of active stocks)
    """
    with db_session() as conn:
        cursor = conn.cursor()

        where_parts = ["active = 1"]
        params: list = []

        if market and market != 'All':
            where_parts.append("market = ?")
            params.append(market)

        if group_id is not None:
            where_parts.append("group_id = ?")
            params.append(group_id)

        where_clause = " WHERE " + " AND ".join(where_parts)

        # Query 1: Get total count
        count_sql = f"SELECT COUNT(*) as cnt FROM stocks{where_clause}"
        cursor.execute(count_sql, params)
        total_count = cursor.fetchone()['cnt']

        # Query 2: Get paginated results
        data_sql = f"""
            SELECT ticker, name, market, group_id, sort_order, added_at, active
            FROM stocks{where_clause}
            ORDER BY sort_order, ticker
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        cursor.execute(data_sql, params)
        stocks = cursor.fetchall()

    return stocks, total_count


def add_stock(ticker: str, name: str, market: str = 'US') -> bool:
    """Add a new stock to monitor"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        ticker = ticker.upper()
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
    Search for stock tickers using Yahoo Finance.
    Returns list of matching stocks with ticker and name.
    """
    try:
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
                if quote.get('quoteType') in ['EQUITY', 'ETF']:
                    results.append({
                        'ticker': quote.get('symbol', ''),
                        'name': quote.get('longname') or quote.get('shortname', ''),
                        'exchange': quote.get('exchange', ''),
                        'type': quote.get('quoteType', '')
                    })

            return results[:10]

    except Exception as e:
        logger.error(f"Error searching for ticker '{query}': {e}")

    return []


# ============================================================================
# Watchlist Groups Functions
# ============================================================================

def create_watchlist_group(name: str, description: Optional[str] = None, color: str = '#6366f1') -> Optional[int]:
    """Create a new watchlist group."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        cursor.execute(
            '''INSERT INTO watchlist_groups (name, description, color)
               VALUES (?, ?, ?)''',
            (name, description, color)
        )

        group_id = cursor.lastrowid
        conn.commit()
        conn.close()
        logger.info(f"Created watchlist group: {name} (ID: {group_id})")
        return group_id
    except sqlite3.IntegrityError:
        logger.error(f"Group name '{name}' already exists")
        return None
    except Exception as e:
        logger.error(f"Error creating watchlist group: {e}")
        return None


def get_watchlist_groups() -> List[Dict]:
    """Get all watchlist groups with stock counts."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT 
                g.id, g.name, g.description, g.color, g.created_at, g.updated_at,
                COUNT(s.ticker) as stock_count
            FROM watchlist_groups g
            LEFT JOIN stocks s ON g.id = s.group_id AND s.active = 1
            GROUP BY g.id
            ORDER BY g.name
        ''')

        groups = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return groups
    except Exception as e:
        logger.error(f"Error getting watchlist groups: {e}")
        return []


def get_watchlist_group_stocks(group_id: int) -> List[str]:
    """Get tickers in a group, ordered by sort_order."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT ticker FROM stocks
            WHERE group_id = ? AND active = 1
            ORDER BY sort_order, ticker
        ''', (group_id,))

        tickers = [row['ticker'] for row in cursor.fetchall()]
        conn.close()
        return tickers
    except Exception as e:
        logger.error(f"Error getting group stocks: {e}")
        return []


def update_watchlist_group(group_id: int, name: Optional[str] = None, 
                          description: Optional[str] = None, color: Optional[str] = None) -> bool:
    """Update a watchlist group."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if color is not None:
            updates.append("color = ?")
            params.append(color)

        if not updates:
            return True

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(group_id)

        sql = f"UPDATE watchlist_groups SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(sql, params)

        conn.commit()
        conn.close()
        logger.info(f"Updated watchlist group {group_id}")
        return True
    except sqlite3.IntegrityError:
        logger.error(f"Group name already exists")
        return False
    except Exception as e:
        logger.error(f"Error updating watchlist group: {e}")
        return False


def delete_watchlist_group(group_id: int) -> bool:
    """Delete a watchlist group (stocks revert to group_id=NULL)."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        # Remove stocks from group
        cursor.execute('UPDATE stocks SET group_id = NULL WHERE group_id = ?', (group_id,))

        # Delete group
        cursor.execute('DELETE FROM watchlist_groups WHERE id = ?', (group_id,))

        conn.commit()
        conn.close()
        logger.info(f"Deleted watchlist group {group_id}")
        return True
    except Exception as e:
        logger.error(f"Error deleting watchlist group: {e}")
        return False


def move_stock_to_group(ticker: str, group_id: Optional[int] = None) -> bool:
    """Move a stock to a group (or remove from group if group_id is None)."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        ticker = ticker.upper()

        # Get next sort_order for this group
        if group_id is not None:
            cursor.execute(
                'SELECT MAX(sort_order) as max_order FROM stocks WHERE group_id = ?',
                (group_id,)
            )
            result = cursor.fetchone()
            next_order = (result['max_order'] or 0) + 1
        else:
            next_order = 0

        cursor.execute(
            'UPDATE stocks SET group_id = ?, sort_order = ? WHERE ticker = ?',
            (group_id, next_order, ticker)
        )

        conn.commit()
        conn.close()
        logger.info(f"Moved stock {ticker} to group {group_id}")
        return True
    except Exception as e:
        logger.error(f"Error moving stock to group: {e}")
        return False


def reorder_stocks_in_group(group_id: int, ticker_order: List[str]) -> bool:
    """Reorder stocks in a group based on ticker list."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        for order, ticker in enumerate(ticker_order):
            cursor.execute(
                'UPDATE stocks SET sort_order = ? WHERE ticker = ? AND group_id = ?',
                (order, ticker.upper(), group_id)
            )

        conn.commit()
        conn.close()
        logger.info(f"Reordered {len(ticker_order)} stocks in group {group_id}")
        return True
    except Exception as e:
        logger.error(f"Error reordering stocks in group: {e}")
        return False


if __name__ == '__main__':
    # Initialize table
    init_stocks_table()

    # Test search
    results = search_stock_ticker('tesla')
    print(f"Search results for 'tesla':")
    for r in results:
        print(f"  {r['ticker']}: {r['name']}")
```