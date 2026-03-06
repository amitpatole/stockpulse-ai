```python
"""
TickerPulse AI v3.0 - Database Connection Manager
Thread-safe SQLite helper with context-manager support and table initialisation.
"""

import sqlite3
import logging
from contextlib import contextmanager

from backend.config import Config

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------

def get_db_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Return a new SQLite connection with Row factory enabled.

    Parameters
    ----------
    db_path : str, optional
        Override the default database path from Config.

    Notes
    -----
    * ``check_same_thread=False`` is required so Flask (and APScheduler)
      threads can share the connection safely.  SQLite itself serialises
      writes, so this is safe for the read-heavy workload of TickerPulse.
    """
    path = db_path or Config.DB_PATH
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')  # better concurrent-read perf
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


@contextmanager
def db_session(db_path: str | None = None):
    """Context manager that yields a connection and auto-closes it.

    Usage::

        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT ...')
            conn.commit()
    """
    conn = get_db_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Table definitions
# ---------------------------------------------------------------------------

# Existing tables (carried over from stock_monitor.py / settings_manager.py)
_EXISTING_TABLES_SQL = [
    # --- news ---
    """
    CREATE TABLE IF NOT EXISTS news (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker          TEXT NOT NULL,
        title           TEXT NOT NULL,
        description     TEXT,
        url             TEXT UNIQUE,
        source          TEXT,
        published_date  TEXT,
        sentiment_score REAL,
        sentiment_label TEXT,
        engagement_score REAL DEFAULT 0,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- alerts ---
    """
    CREATE TABLE IF NOT EXISTS alerts (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker      TEXT NOT NULL,
        news_id     INTEGER,
        alert_type  TEXT,
        message     TEXT,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (news_id) REFERENCES news (id)
    )
    """,
    # --- monitor_status ---
    """
    CREATE TABLE IF NOT EXISTS monitor_status (
        id          INTEGER PRIMARY KEY,
        last_check  TIMESTAMP,
        status      TEXT,
        message     TEXT
    )
    """,
    # --- stocks ---
    """
    CREATE TABLE IF NOT EXISTS stocks (
        ticker   TEXT PRIMARY KEY,
        name     TEXT,
        market   TEXT DEFAULT 'US',
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        active   INTEGER DEFAULT 1
    )
    """,
    # --- settings ---
    """
    CREATE TABLE IF NOT EXISTS settings (
        key        TEXT PRIMARY KEY,
        value      TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- ai_providers ---
    """
    CREATE TABLE IF NOT EXISTS ai_providers (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_name TEXT NOT NULL,
        api_key       TEXT NOT NULL,
        model         TEXT,
        is_active     INTEGER DEFAULT 0,
        created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
]

# New v3.0 tables
_NEW_TABLES_SQL = [
    # --- agent_runs: tracks every AI agent execution ---
    """
    CREATE TABLE IF NOT EXISTS agent_runs (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_name      TEXT NOT NULL,
        framework       TEXT NOT NULL DEFAULT 'crewai',  -- 'crewai' | 'openclaw'
        status          TEXT NOT NULL DEFAULT 'pending',  -- pending | running | completed | failed
        input_data      TEXT,       -- JSON
        output_data     TEXT,       -- JSON
        tokens_input    INTEGER DEFAULT 0,
        tokens_output   INTEGER DEFAULT 0,
        estimated_cost  REAL    DEFAULT 0.0,
        duration_ms     INTEGER DEFAULT 0,
        error           TEXT,
        metadata        TEXT,       -- JSON
        started_at      TIMESTAMP,
        completed_at    TIMESTAMP,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- job_history: scheduler / cron job audit log ---
    """
    CREATE TABLE IF NOT EXISTS job_history (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id          TEXT NOT NULL,
        job_name        TEXT NOT NULL,
        status          TEXT NOT NULL DEFAULT 'pending',  -- pending | running | completed | failed
        result_summary  TEXT,       -- short human-readable outcome
        agent_name      TEXT,       -- NULL when job does not involve an agent
        duration_ms     INTEGER DEFAULT 0,
        cost            REAL    DEFAULT 0.0,
        executed_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- data_providers_config: market-data provider registry ---
    """
    CREATE TABLE IF NOT EXISTS data_providers_config (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        provider_name         TEXT NOT NULL UNIQUE,
        api_key               TEXT DEFAULT '',
        is_active             INTEGER DEFAULT 1,
        is_primary            INTEGER DEFAULT 0,
        priority              INTEGER DEFAULT 100,  -- lower = higher priority (fallback order)
        rate_limit_remaining  INTEGER DEFAULT -1,    -- -1 = unknown / unlimited
        last_used             TIMESTAMP,
        created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- research_briefs: AI-generated research reports ---
    """
    CREATE TABLE IF NOT EXISTS research_briefs (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker          TEXT NOT NULL,
        title           TEXT NOT NULL,
        content         TEXT NOT NULL,
        agent_name      TEXT NOT NULL DEFAULT 'researcher',
        model_used      TEXT,
        tokens_used     INTEGER DEFAULT 0,
        estimated_cost  REAL    DEFAULT 0.0,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- ai_ratings: cached AI ratings for stocks ---
    """
    CREATE TABLE IF NOT EXISTS ai_ratings (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker          TEXT NOT NULL UNIQUE,
        rating          TEXT NOT NULL DEFAULT 'HOLD',
        score           REAL NOT NULL DEFAULT 0,
        confidence      REAL NOT NULL DEFAULT 0,
        current_price   REAL,
        price_change    REAL,
        price_change_pct REAL,
        rsi             REAL,
        sentiment_score REAL,
        sentiment_label TEXT,
        technical_score REAL,
        fundamental_score REAL,
        summary         TEXT,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- cost_tracking: per-call cost ledger ---
    """
    CREATE TABLE IF NOT EXISTS cost_tracking (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        date            TEXT NOT NULL,       -- YYYY-MM-DD
        agent_name      TEXT,
        provider_name   TEXT,
        model           TEXT,
        tokens_input    INTEGER DEFAULT 0,
        tokens_output   INTEGER DEFAULT 0,
        estimated_cost  REAL    DEFAULT 0.0,
        job_name        TEXT,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- download_stats: aggregate repository download statistics ---
    """
    CREATE TABLE IF NOT EXISTS download_stats (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        repo_owner      TEXT NOT NULL,
        repo_name       TEXT NOT NULL,
        total_clones    INTEGER DEFAULT 0,
        unique_clones   INTEGER DEFAULT 0,
        period_start    TIMESTAMP,
        period_end      TIMESTAMP,
        recorded_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # --- download_daily: daily breakdown of repository downloads ---
    """
    CREATE TABLE IF NOT EXISTS download_daily (
        repo_owner      TEXT NOT NULL,
        repo_name       TEXT NOT NULL,
        date            TEXT NOT NULL,       -- YYYY-MM-DD
        clones          INTEGER DEFAULT 0,
        unique_clones   INTEGER DEFAULT 0,
        PRIMARY KEY (repo_owner, repo_name, date)
    )
    """,
    # --- watchlist_groups: named groups for organizing stocks ---
    """
    CREATE TABLE IF NOT EXISTS watchlist_groups (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT NOT NULL UNIQUE,
        position        INTEGER NOT NULL DEFAULT 0,
        created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
]

# Useful indices for the new tables
_INDEXES_SQL = [
    "CREATE INDEX IF NOT EXISTS idx_agent_runs_status      ON agent_runs (status)",
    "CREATE INDEX IF NOT EXISTS idx_agent_runs_agent       ON agent_runs (agent_name)",
    "CREATE INDEX IF NOT EXISTS idx_agent_runs_started     ON agent_runs (started_at)",
    "CREATE INDEX IF NOT EXISTS idx_job_history_job_id     ON job_history (job_id)",
    "CREATE INDEX IF NOT EXISTS idx_job_history_executed   ON job_history (executed_at)",
    "CREATE INDEX IF NOT EXISTS idx_cost_tracking_date     ON cost_tracking (date)",
    "CREATE INDEX IF NOT EXISTS idx_cost_tracking_agent    ON cost_tracking (agent_name)",
    "CREATE INDEX IF NOT EXISTS idx_ai_ratings_ticker       ON ai_ratings (ticker)",
    "CREATE INDEX IF NOT EXISTS idx_news_ticker            ON news (ticker)",
    "CREATE INDEX IF NOT EXISTS idx_news_created           ON news (created_at)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_created         ON alerts (created_at)",
    "CREATE INDEX IF NOT EXISTS idx_download_stats_repo    ON download_stats (repo_owner, repo_name)",
    "CREATE INDEX IF NOT EXISTS idx_download_stats_date    ON download_stats (recorded_at)",
    "CREATE INDEX IF NOT EXISTS idx_download_daily_date    ON download_daily (date)",
    "CREATE INDEX IF NOT EXISTS idx_watchlist_groups_position ON watchlist_groups (position)",
]


# ---------------------------------------------------------------------------
# Migration functions
# ---------------------------------------------------------------------------

def _migrate_agent_runs(cursor: sqlite3.Cursor) -> None:
    """Migrate agent_runs from v3.0.0 schema (tokens_used) to v3.0.1 (tokens_input/tokens_output).

    Safe to call multiple times — silently skips if columns already exist.
    """
    # Check existing columns
    cols = {row[1] for row in cursor.execute("PRAGMA table_info(agent_runs)").fetchall()}
    if not cols:
        return  # table doesn't exist yet, CREATE TABLE will handle it

    migrations = []
    if 'tokens_input' not in cols:
        migrations.append("ALTER TABLE agent_runs ADD COLUMN tokens_input INTEGER DEFAULT 0")
    if 'tokens_output' not in cols:
        migrations.append("ALTER TABLE agent_runs ADD COLUMN tokens_output INTEGER DEFAULT 0")
    if 'error' not in cols:
        migrations.append("ALTER TABLE agent_runs ADD COLUMN error TEXT")
    if 'metadata' not in cols:
        migrations.append("ALTER TABLE agent_runs ADD COLUMN metadata TEXT")

    # Copy data from old tokens_used into tokens_input if migrating
    if 'tokens_used' in cols and 'tokens_input' not in cols:
        migrations.append("UPDATE agent_runs SET tokens_input = tokens_used WHERE tokens_used > 0")

    for sql in migrations:
        cursor.execute(sql)
        logger.info(f"Migration applied: {sql}")


def _migrate_news(cursor: sqlite3.Cursor) -> None:
    """Add engagement_score column to news table if missing."""
    cols = {row[1] for row in cursor.execute("PRAGMA table_info(news)").fetchall()}
    if not cols:
        return
    if 'engagement_score' not in cols:
        cursor.execute("ALTER TABLE news ADD COLUMN engagement_score REAL DEFAULT 0")
        logger.info("Migration applied: added engagement_score to news table")


def _migrate_research_briefs(cursor: sqlite3.Cursor) -> None:
    """Add executive_summary and key_metrics columns to research_briefs if missing."""
    cols = {row[1] for row in cursor.execute("PRAGMA table_info(research_briefs)").fetchall()}
    if not cols:
        return  # table doesn't exist yet, CREATE TABLE will handle it

    migrations = []
    if 'executive_summary' not in cols:
        migrations.append("ALTER TABLE research_briefs ADD COLUMN executive_summary TEXT")
    if 'key_metrics' not in cols:
        migrations.append("ALTER TABLE research_briefs ADD COLUMN key_metrics TEXT")  # JSON stored as TEXT

    for sql in migrations:
        cursor.execute(sql)
        logger.info(f"Migration applied: {sql}")


def _migrate_stocks(cursor: sqlite3.Cursor) -> None:
    """Add group_id and position columns to stocks table if missing."""
    cols = {row[1] for row in cursor.execute("PRAGMA table_info(stocks)").fetchall()}
    if not cols:
        return  # table doesn't exist yet, CREATE TABLE will handle it

    migrations = []
    if 'group_id' not in cols:
        migrations.append("ALTER TABLE stocks ADD COLUMN group_id INTEGER")
    if 'position' not in cols:
        migrations.append("ALTER TABLE stocks ADD COLUMN position INTEGER DEFAULT 0")

    for sql in migrations:
        cursor.execute(sql)
        logger.info(f"Migration applied: {sql}")


def init_all_tables(db_path: str | None = None) -> None:
    """Create every table (existing + new v3.0) and apply indexes.

    Safe to call multiple times -- all statements use
    ``CREATE TABLE IF NOT EXISTS`` / ``CREATE INDEX IF NOT EXISTS``.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        for sql in _EXISTING_TABLES_SQL:
            cursor.execute(sql)

        # Migrate existing tables before CREATE TABLE (which is a no-op if table exists)
        _migrate_agent_runs(cursor)
        _migrate_news(cursor)
        _migrate_research_briefs(cursor)
        _migrate_stocks(cursor)

        for sql in _NEW_TABLES_SQL:
            cursor.execute(sql)

        for sql in _INDEXES_SQL:
            cursor.execute(sql)

        conn.commit()
        logger.info("All database tables and indexes initialised successfully")
    except Exception:
        conn.rollback()
        logger.exception("Failed to initialise database tables")
        raise
    finally:
        conn.close()
```

--- FILE: backend/core/stock_manager.py (updated) ---

```python
#!/usr/bin/env python3
"""
Stock Manager - Handles dynamic stock list management and watchlist groups
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


# ---------------------------------------------------------------------------
# Watchlist Groups Functions
# ---------------------------------------------------------------------------

def create_watchlist_group(name: str) -> Optional[Dict]:
    """Create a new watchlist group.
    
    Parameters
    ----------
    name : str
        The name of the watchlist group (must be unique).
    
    Returns
    -------
    Optional[Dict]
        Dictionary with group details (id, name, position, created_at) if successful, None otherwise.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get the next position (max existing position + 1)
        cursor.execute('SELECT MAX(position) as max_pos FROM watchlist_groups')
        result = cursor.fetchone()
        next_position = (result['max_pos'] or -1) + 1

        # Insert new group
        cursor.execute(
            'INSERT INTO watchlist_groups (name, position) VALUES (?, ?)',
            (name, next_position)
        )
        conn.commit()

        # Retrieve inserted group
        group_id = cursor.lastrowid
        cursor.execute('SELECT * FROM watchlist_groups WHERE id = ?', (group_id,))
        group = dict(cursor.fetchone())
        conn.close()

        logger.info(f"Created watchlist group: {name} (ID: {group_id})")
        return group

    except sqlite3.IntegrityError:
        logger.error(f"Watchlist group '{name}' already exists")
        return None
    except Exception as e:
        logger.error(f"Error creating watchlist group '{name}': {e}")
        return None


def get_all_watchlist_groups() -> List[Dict]:
    """Get all watchlist groups ordered by position.
    
    Returns
    -------
    List[Dict]
        List of group dictionaries with id, name, position, created_at, updated_at.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM watchlist_groups ORDER BY position ASC')
        groups = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return groups

    except Exception as e:
        logger.error(f"Error fetching watchlist groups: {e}")
        return []


def get_watchlist_group(group_id: int) -> Optional[Dict]:
    """Get a single watchlist group by ID.
    
    Parameters
    ----------
    group_id : int
        The ID of the watchlist group.
    
    Returns
    -------
    Optional[Dict]
        Group dictionary if found, None otherwise.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM watchlist_groups WHERE id = ?', (group_id,))
        result = cursor.fetchone()
        conn.close()

        return dict(result) if result else None

    except Exception as e:
        logger.error(f"Error fetching watchlist group {group_id}: {e}")
        return None


def update_watchlist_group(group_id: int, name: str) -> Optional[Dict]:
    """Update a watchlist group's name.
    
    Parameters
    ----------
    group_id : int
        The ID of the watchlist group.
    name : str
        The new name for the group.
    
    Returns
    -------
    Optional[Dict]
        Updated group dictionary if successful, None otherwise.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            'UPDATE watchlist_groups SET name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (name, group_id)
        )
        conn.commit()

        # Fetch updated group
        cursor.execute('SELECT * FROM watchlist_groups WHERE id = ?', (group_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            logger.info(f"Updated watchlist group {group_id}: {name}")
            return dict(result)
        return None

    except sqlite3.IntegrityError:
        logger.error(f"Watchlist group name '{name}' already exists")
        return None
    except Exception as e:
        logger.error(f"Error updating watchlist group {group_id}: {e}")
        return None


def delete_watchlist_group(group_id: int) -> bool:
    """Delete a watchlist group and unassign all stocks from it.
    
    Parameters
    ----------
    group_id : int
        The ID of the watchlist group to delete.
    
    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        # Remove group_id from all stocks in this group
        cursor.execute('UPDATE stocks SET group_id = NULL, position = 0 WHERE group_id = ?', (group_id,))

        # Delete the group
        cursor.execute('DELETE FROM watchlist_groups WHERE id = ?', (group_id,))

        conn.commit()
        conn.close()

        logger.info(f"Deleted watchlist group {group_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting watchlist group {group_id}: {e}")
        return False


def add_stock_to_group(ticker: str, group_id: int, position: int = 0) -> bool:
    """Add a stock to a watchlist group.
    
    Parameters
    ----------
    ticker : str
        The stock ticker.
    group_id : int
        The ID of the watchlist group.
    position : int
        The position within the group (default: 0).
    
    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        ticker = ticker.upper()
        cursor.execute(
            'UPDATE stocks SET group_id = ?, position = ? WHERE ticker = ?',
            (group_id, position, ticker)
        )
        conn.commit()
        conn.close()

        logger.info(f"Added stock {ticker} to group {group_id} at position {position}")
        return True

    except Exception as e:
        logger.error(f"Error adding stock {ticker} to group {group_id}: {e}")
        return False


def remove_stock_from_group(ticker: str) -> bool:
    """Remove a stock from its watchlist group.
    
    Parameters
    ----------
    ticker : str
        The stock ticker.
    
    Returns
    -------
    bool
        True if successful, False otherwise.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        ticker = ticker.upper()
        cursor.execute(
            'UPDATE stocks SET group_id = NULL, position = 0 WHERE ticker = ?',
            (ticker,)
        )
        conn.commit()
        conn.close()

        logger.info(f"Removed stock {ticker} from its group")
        return True

    except Exception as e:
        logger.error(f"Error removing stock {ticker} from group: {e}")
        return False


def reorder_group_stocks(group_id: int, ticker_positions: List[Dict]) -> bool:
    """Update positions for multiple stocks in a group (for drag-and-drop reordering).
    
    Parameters
    ----------
    group_id : int
        The ID of the watchlist group.
    ticker_positions : List[Dict]
        List of dicts with 'ticker' and 'position' keys.
        Example: [{'ticker': 'AAPL', 'position': 0}, {'ticker': 'MSFT', 'position': 1}]
    
    Returns
    -------
    bool
        True if all updates successful, False otherwise.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()

        for item in ticker_positions:
            ticker = item.get('ticker', '').upper()
            position = item.get('position', 0)

            cursor.execute(
                'UPDATE stocks SET position = ? WHERE ticker = ? AND group_id = ?',
                (position, ticker, group_id)
            )

        conn.commit()
        conn.close()

        logger.info(f"Reordered {len(ticker_positions)} stocks in group {group_id}")
        return True

    except Exception as e:
        logger.error(f"Error reordering stocks in group {group_id}: {e}")
        return False


def get_group_stocks(group_id: int) -> List[Dict]:
    """Get all stocks in a watchlist group, ordered by position.
    
    Parameters
    ----------
    group_id : int
        The ID of the watchlist group.
    
    Returns
    -------
    List[Dict]
        List of stock dictionaries ordered by position.
    """
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM stocks WHERE group_id = ? AND active = 1 ORDER BY position ASC',
            (group_id,)
        )
        stocks = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return stocks

    except Exception as e:
        logger.error(f"Error fetching stocks in group {group_id}: {e}")
        return []


if __name__ == '__main__':
    # Initialize table
    init_stocks_table()

    # Test search
    results = search_stock_ticker('tesla')
    print(f"Search results for 'tesla':")
    for r in results:
        print(f"  {r['ticker']}: {r['name']}")
```

--- FILE: backend/api/stocks.py (updated) ---

```python
"""
TickerPulse AI v3.0 - Stocks API Routes
Blueprint for stock management endpoints: list, add, remove, search stocks, and manage watchlist groups.
"""

from flask import Blueprint, jsonify, request
import logging
from typing import Dict, Any

from backend.core.stock_manager import (
    get_all_stocks, add_stock, remove_stock, search_stock_ticker,
    create_watchlist_group, get_all_watchlist_groups, get_watchlist_group,
    update_watchlist_group, delete_watchlist_group, add_stock_to_group,
    remove_stock_from_group, reorder_group_stocks, get_group_stocks
)

logger = logging.getLogger(__name__)

stocks_bp = Blueprint('stocks', __name__, url_prefix='/api')


# ---------------------------------------------------------------------------
# Stock Endpoints
# ---------------------------------------------------------------------------

@stocks_bp.route('/stocks', methods=['GET'])
def get_stocks():
    """Get all monitored stocks.

    Query Parameters:
        market (str, optional): Filter by market (e.g. 'US', 'India'). 'All' returns everything.

    Returns:
        JSON array of stock objects with ticker, name, market, added_at, active fields.
    """
    market = request.args.get('market', None)
    stocks = get_all_stocks()

    # Filter by market if specified
    if market and market != 'All':
        stocks = [s for s in stocks if s.get('market') == market]

    return jsonify(stocks)


@stocks_bp.route('/stocks', methods=['POST'])
def add_stock_endpoint():
    """Add a new stock to the monitored list.

    Request Body (JSON):
        ticker (str): Stock ticker symbol (e.g. 'AAPL', 'RELIANCE.NS')
        name (str, optional): Company name. Validated via Yahoo Finance if omitted.
        market (str, optional): Market identifier, defaults to 'US'

    Returns:
        JSON object with 'success' boolean and stock details.
        Returns 404 if ticker is not found on any exchange.
    """
    data = request.json
    if not data or 'ticker' not in data:
        return jsonify({'success': False, 'error': 'Missing required field: ticker'}), 400

    ticker = data['ticker'].strip().upper()
    name = data.get('name')

    # Validate ticker exists and look up name if not provided
    if not name:
        results = search_stock_ticker(ticker)
        # Check for an exact ticker match
        match = next((r for r in results if r['ticker'].upper() == ticker), None)
        if match:
            name = match.get('name', ticker)
        elif results:
            # No exact match — reject with suggestions
            suggestions = [f"{r['ticker']} ({r['name']})" for r in results[:3]]
            return jsonify({
                'success': False,
                'error': f"Ticker '{ticker}' not found. Did you mean: {', '.join(suggestions)}?"
            }), 404
        else:
            return jsonify({
                'success': False,
                'error': f"Ticker '{ticker}' not found on any exchange."
            }), 404

    market = data.get('market', 'US')
    success = add_stock(ticker, name, market)
    return jsonify({'success': success, 'ticker': ticker, 'name': name, 'market': market})


@stocks_bp.route('/stocks/<ticker>', methods=['DELETE'])
def remove_stock_endpoint(ticker: str):
    """Remove a stock from monitoring (soft delete).

    Path Parameters:
        ticker (str): Stock ticker symbol to remove.

    Returns:
        JSON object with 'success' boolean.
    """
    success = remove_stock(ticker)
    return jsonify({'success': success})


@stocks_bp.route('/stocks/search', methods=['GET'])
def search_stocks():
    """Search for stock tickers via Yahoo Finance.

    Query Parameters:
        q (str): Search query string (company name or ticker fragment).

    Returns:
        JSON array of matching stocks with ticker, name, exchange, type fields.
        Returns empty array if query is empty.
    """
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    results = search_stock_ticker(query)
    return jsonify(results)


# ---------------------------------------------------------------------------
# Watchlist Groups Endpoints
# ---------------------------------------------------------------------------

@stocks_bp.route('/watchlist-groups', methods=['GET'])
def get_groups():
    """Get all watchlist groups ordered by position.

    Returns:
        JSON array of group objects with id, name, position, created_at, updated_at.
    """
    groups = get_all_watchlist_groups()
    return jsonify(groups)


@stocks_bp.route('/watchlist-groups', methods=['POST'])
def create_group():
    """Create a new watchlist group.

    Request Body (JSON):
        name (str): The name of the new watchlist group (must be unique).

    Returns:
        JSON object with group details if successful.
        Returns 400 if name is missing or 409 if name already exists.
    """
    data = request.json
    if not data or 'name' not in data:
        return jsonify({'success': False, 'error': 'Missing required field: name'}), 400

    name = data['name'].strip()
    if not name:
        return jsonify({'success': False, 'error': 'Group name cannot be empty'}), 400

    group = create_watchlist_group(name)
    if group:
        return jsonify({'success': True, 'group': group}), 201
    else:
        return jsonify({'success': False, 'error': f"Group '{name}' already exists"}), 409


@stocks_bp.route('/watchlist-groups/<int:group_id>', methods=['GET'])
def get_group(group_id: int):
    """Get a single watchlist group by ID.

    Path Parameters:
        group_id (int): The ID of the watchlist group.

    Returns:
        JSON object with group details if found, 404 if not found.
    """
    group = get_watchlist_group(group_id)
    if group:
        return jsonify(group)
    else:
        return jsonify({'error': 'Group not found'}), 404


@stocks_bp.route('/watchlist-groups/<int:group_id>', methods=['PUT'])
def update_group(group_id: int):
    """Update a watchlist group's name.

    Path Parameters:
        group_id (int): The ID of the watchlist group.

    Request Body (JSON):
        name (str): The new name for the group.

    Returns:
        JSON object with updated group details if successful.
        Returns 404 if group not found, 409 if name already exists.
    """
    data = request.json
    if not data or 'name' not in data:
        return jsonify({'error': 'Missing required field: name'}), 400

    name = data['name'].strip()
    if not name:
        return jsonify({'error': 'Group name cannot be empty'}), 400

    group = update_watchlist_group(group_id, name)
    if group:
        return jsonify({'success': True, 'group': group})
    else:
        return jsonify({'error': 'Group not found or name already exists'}), 404


@stocks_bp.route('/watchlist-groups/<int:group_id>', methods=['DELETE'])
def delete_group(group_id: int):
    """Delete a watchlist group.

    Path Parameters:
        group_id (int): The ID of the watchlist group to delete.

    Returns:
        JSON object with success status. All stocks in the group are unassigned.
    """
    success = delete_watchlist_group(group_id)
    if success:
        return jsonify({'success': True}), 204
    else:
        return jsonify({'success': False, 'error': 'Failed to delete group'}), 500


@stocks_bp.route('/watchlist-groups/<int:group_id>/stocks', methods=['GET'])
def get_group_stocks_endpoint(group_id: int):
    """Get all stocks in a watchlist group, ordered by position.

    Path Parameters:
        group_id (int): The ID of the watchlist group.

    Returns:
        JSON array of stock objects in the group ordered by position.
    """
    stocks = get_group_stocks(group_id)
    return jsonify(stocks)


@stocks_bp.route('/watchlist-groups/<int:group_id>/stocks', methods=['POST'])
def add_stock_to_group_endpoint(group_id: int):
    """Add a stock to a watchlist group.

    Path Parameters:
        group_id (int): The ID of the watchlist group.

    Request Body (JSON):
        ticker (str): The stock ticker to add.
        position (int, optional): Position in the group (default: 0).

    Returns:
        JSON object with success status.
    """
    data = request.json
    if not data or 'ticker' not in data:
        return jsonify({'success': False, 'error': 'Missing required field: ticker'}), 400

    ticker = data['ticker'].strip().upper()
    position = data.get('position', 0)

    success = add_stock_to_group(ticker, group_id, position)
    if success:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'error': 'Failed to add stock to group'}), 500


@stocks_bp.route('/watchlist-groups/<int:group_id>/stocks/<ticker>', methods=['DELETE'])
def remove_stock_from_group_endpoint(group_id: int, ticker: str):
    """Remove a stock from a watchlist group.

    Path Parameters:
        group_id (int): The ID of the watchlist group.
        ticker (str): The stock ticker to remove.

    Returns:
        JSON object with success status.
    """
    success = remove_stock_from_group(ticker)
    if success:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'error': 'Failed to remove stock from group'}), 500


@stocks_bp.route('/watchlist-groups/<int:group_id>/reorder', methods=['POST'])
def reorder_stocks(group_id: int):
    """Batch reorder stocks within a watchlist group (for drag-and-drop).

    Path Parameters:
        group_id (int): The ID of the watchlist group.

    Request Body (JSON):
        stocks (List[Dict]): List of {ticker, position} objects.
        Example: [{"ticker": "AAPL", "position": 0}, {"ticker": "MSFT", "position": 1}]

    Returns:
        JSON object with success status.
    """
    data = request.json
    if not data or 'stocks' not in data:
        return jsonify({'success': False, 'error': 'Missing required field: stocks'}), 400

    stocks_list = data['stocks']
    if not isinstance(stocks_list, list):
        return jsonify({'success': False, 'error': 'stocks must be an array'}), 400

    success = reorder_group_stocks(group_id, stocks_list)
    if success:
        return jsonify({'success': True}), 200
    else:
        return jsonify({'success': False, 'error': 'Failed to reorder stocks'}), 500
```