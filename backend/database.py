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
]

# Comprehensive indexes for query optimization
_INDEXES_SQL = [
    # --- stocks table indexes ---
    "CREATE INDEX IF NOT EXISTS idx_stocks_active         ON stocks (active)",
    "CREATE INDEX IF NOT EXISTS idx_stocks_market         ON stocks (market)",
    "CREATE INDEX IF NOT EXISTS idx_stocks_active_market  ON stocks (active, market)",
    
    # --- agent_runs indexes ---
    "CREATE INDEX IF NOT EXISTS idx_agent_runs_status      ON agent_runs (status)",
    "CREATE INDEX IF NOT EXISTS idx_agent_runs_agent       ON agent_runs (agent_name)",
    "CREATE INDEX IF NOT EXISTS idx_agent_runs_started     ON agent_runs (started_at)",
    "CREATE INDEX IF NOT EXISTS idx_agent_runs_status_agent ON agent_runs (status, agent_name)",
    
    # --- job_history indexes ---
    "CREATE INDEX IF NOT EXISTS idx_job_history_job_id     ON job_history (job_id)",
    "CREATE INDEX IF NOT EXISTS idx_job_history_executed   ON job_history (executed_at)",
    "CREATE INDEX IF NOT EXISTS idx_job_history_status     ON job_history (status)",
    "CREATE INDEX IF NOT EXISTS idx_job_history_job_status ON job_history (job_id, status)",
    
    # --- cost_tracking indexes ---
    "CREATE INDEX IF NOT EXISTS idx_cost_tracking_date     ON cost_tracking (date)",
    "CREATE INDEX IF NOT EXISTS idx_cost_tracking_agent    ON cost_tracking (agent_name)",
    "CREATE INDEX IF NOT EXISTS idx_cost_tracking_date_agent ON cost_tracking (date, agent_name)",
    
    # --- ai_ratings indexes ---
    "CREATE INDEX IF NOT EXISTS idx_ai_ratings_ticker       ON ai_ratings (ticker)",
    "CREATE INDEX IF NOT EXISTS idx_ai_ratings_updated      ON ai_ratings (updated_at)",
    "CREATE INDEX IF NOT EXISTS idx_ai_ratings_ticker_updated ON ai_ratings (ticker, updated_at DESC)",
    
    # --- research_briefs indexes (ADDED) ---
    "CREATE INDEX IF NOT EXISTS idx_research_briefs_ticker  ON research_briefs (ticker)",
    "CREATE INDEX IF NOT EXISTS idx_research_briefs_created ON research_briefs (created_at)",
    "CREATE INDEX IF NOT EXISTS idx_research_briefs_ticker_created ON research_briefs (ticker, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_research_briefs_ticker_agent ON research_briefs (ticker, agent_name, created_at DESC)",
    
    # --- news indexes ---
    "CREATE INDEX IF NOT EXISTS idx_news_ticker            ON news (ticker)",
    "CREATE INDEX IF NOT EXISTS idx_news_created           ON news (created_at)",
    "CREATE INDEX IF NOT EXISTS idx_news_ticker_created    ON news (ticker, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_news_ticker_sentiment_date ON news (ticker, sentiment_label, created_at DESC)",
    
    # --- alerts indexes ---
    "CREATE INDEX IF NOT EXISTS idx_alerts_created         ON alerts (created_at)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_ticker          ON alerts (ticker)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_ticker_created  ON alerts (ticker, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_alerts_news_id         ON alerts (news_id)",
    
    # --- ai_providers indexes (ADDED) ---
    "CREATE INDEX IF NOT EXISTS idx_ai_providers_active    ON ai_providers (is_active)",
    
    # --- data_providers_config indexes (ADDED) ---
    "CREATE INDEX IF NOT EXISTS idx_providers_config_active ON data_providers_config (is_active)",
    "CREATE INDEX IF NOT EXISTS idx_providers_config_primary ON data_providers_config (is_primary)",
    "CREATE INDEX IF NOT EXISTS idx_providers_config_priority ON data_providers_config (priority)",
    
    # --- download_stats indexes ---
    "CREATE INDEX IF NOT EXISTS idx_download_stats_repo    ON download_stats (repo_owner, repo_name)",
    "CREATE INDEX IF NOT EXISTS idx_download_stats_date    ON download_stats (recorded_at)",
    
    # --- download_daily indexes ---
    "CREATE INDEX IF NOT EXISTS idx_download_daily_date    ON download_daily (date)",
    "CREATE INDEX IF NOT EXISTS idx_download_daily_repo_date ON download_daily (repo_owner, repo_name, date)",
]


# ---------------------------------------------------------------------------
# Public initialisation function
# ---------------------------------------------------------------------------

def _migrate_agent_runs(cursor) -> None:
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


def _migrate_news(cursor) -> None:
    """Add engagement_score column to news table if missing."""
    cols = {row[1] for row in cursor.execute("PRAGMA table_info(news)").fetchall()}
    if not cols:
        return
    if 'engagement_score' not in cols:
        cursor.execute("ALTER TABLE news ADD COLUMN engagement_score REAL DEFAULT 0")
        logger.info("Migration applied: added engagement_score to news table")


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

--- FILE: backend/core/query_optimizer.py ---
```python
"""
TickerPulse AI v3.0 - Query Optimization Utilities
Provides helpers for efficient database queries: batching, column selection, pagination.
"""

import logging
from typing import Any, Dict, List, Optional, TypeVar

from backend.database import db_session

logger = logging.getLogger(__name__)

T = TypeVar('T')


def get_active_stocks_optimized(
    market: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[List[Dict[str, Any]], int]:
    """
    Fetch active stocks with optional market filtering (SQL-side, not Python).
    
    Args:
        market: Optional market filter (e.g., 'US', 'India'). If None or 'All', no filter.
        limit: Max records to return (default 100)
        offset: Number of records to skip (default 0)
    
    Returns:
        Tuple of (stocks_list, total_count)
    """
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Build WHERE clause dynamically
        where_clause = "WHERE active = 1"
        params: List[Any] = []
        
        if market and market != 'All':
            where_clause += " AND market = ?"
            params.append(market)
        
        # Get total count for pagination
        count_sql = f"SELECT COUNT(*) as count FROM stocks {where_clause}"
        count_row = cursor.execute(count_sql, params).fetchone()
        total_count = count_row['count'] if count_row else 0
        
        # Get paginated results with only needed columns
        select_sql = f"""
            SELECT ticker, name, market, added_at, active 
            FROM stocks 
            {where_clause} 
            ORDER BY ticker 
            LIMIT ? OFFSET ?
        """
        params.extend([limit, offset])
        rows = cursor.execute(select_sql, params).fetchall()
        
        stocks = [dict(row) for row in rows]
    
    return stocks, total_count


def get_cached_ratings_optimized(ticker: str | None = None) -> List[Dict[str, Any]]:
    """
    Fetch AI ratings with optional ticker filter (SQL-side filtering).
    Selects only needed columns to reduce data transfer.
    
    Args:
        ticker: Optional ticker to filter by. If None, returns all.
    
    Returns:
        List of rating dicts
    """
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Select only the columns actually used in the response
        columns = """
            ticker, rating, score, confidence, current_price, price_change,
            price_change_pct, rsi, sentiment_score, sentiment_label,
            technical_score, fundamental_score, updated_at
        """
        
        if ticker:
            sql = f"SELECT {columns} FROM ai_ratings WHERE ticker = ? ORDER BY ticker"
            rows = cursor.execute(sql, (ticker.upper(),)).fetchall()
        else:
            sql = f"SELECT {columns} FROM ai_ratings ORDER BY ticker"
            rows = cursor.execute(sql).fetchall()
        
        ratings = [
            {
                'ticker': r['ticker'],
                'rating': r['rating'],
                'score': r['score'] or 0,
                'confidence': r['confidence'] or 0,
                'current_price': r['current_price'] or 0,
                'price_change': r['price_change'] or 0,
                'price_change_pct': r['price_change_pct'] or 0,
                'rsi': r['rsi'] or 0,
                'sentiment_score': r['sentiment_score'] or 0,
                'sentiment_label': r['sentiment_label'] or 'neutral',
                'technical_score': r['technical_score'] or 0,
                'fundamental_score': r['fundamental_score'] or 0,
                'updated_at': r['updated_at'],
            }
            for r in rows
        ]
    
    return ratings


def batch_get_stocks_by_tickers(tickers: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch multiple stocks by ticker in a single query (avoids N+1).
    
    Args:
        tickers: List of stock tickers to fetch
    
    Returns:
        Dict mapping ticker -> stock_dict
    """
    if not tickers:
        return {}
    
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Use parameterized query with IN clause (one query, not N queries)
        placeholders = ','.join('?' * len(tickers))
        sql = f"SELECT * FROM stocks WHERE ticker IN ({placeholders}) AND active = 1"
        
        rows = cursor.execute(sql, tickers).fetchall()
        stocks = {row['ticker']: dict(row) for row in rows}
    
    return stocks


def count_active_stocks() -> int:
    """Get count of active stocks efficiently."""
    with db_session() as conn:
        cursor = conn.cursor()
        count_row = cursor.execute(
            "SELECT COUNT(*) as count FROM stocks WHERE active = 1"
        ).fetchone()
        return count_row['count'] if count_row else 0


def get_active_ai_providers() -> List[Dict[str, Any]]:
    """
    Fetch only active AI providers (indexes on is_active for efficiency).
    
    Returns:
        List of active provider dicts
    """
    with db_session() as conn:
        cursor = conn.cursor()
        
        sql = """
            SELECT id, provider_name, model, is_active, updated_at
            FROM ai_providers 
            WHERE is_active = 1 
            ORDER BY provider_name
        """
        rows = cursor.execute(sql).fetchall()
        providers = [dict(row) for row in rows]
    
    return providers


def get_primary_data_provider() -> Optional[Dict[str, Any]]:
    """
    Get the primary data provider efficiently using indexes.
    
    Returns:
        Primary provider dict or None if not found
    """
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Uses indexes on is_active and is_primary
        sql = """
            SELECT id, provider_name, api_key, is_active, priority
            FROM data_providers_config 
            WHERE is_active = 1 AND is_primary = 1
            ORDER BY priority
            LIMIT 1
        """
        row = cursor.execute(sql).fetchone()
        return dict(row) if row else None


def get_research_briefs_by_ticker(
    ticker: str,
    limit: int = 25,
    offset: int = 0,
) -> tuple[List[Dict[str, Any]], int]:
    """
    Fetch research briefs for a ticker with pagination (uses composite index).
    
    Args:
        ticker: Stock ticker to fetch briefs for
        limit: Max records per page
        offset: Pagination offset
    
    Returns:
        Tuple of (briefs_list, total_count)
    """
    with db_session() as conn:
        cursor = conn.cursor()
        
        ticker_upper = ticker.upper()
        
        # Get total count
        count_row = cursor.execute(
            "SELECT COUNT(*) as count FROM research_briefs WHERE ticker = ?",
            (ticker_upper,)
        ).fetchone()
        total_count = count_row['count'] if count_row else 0
        
        # Use composite index (ticker, created_at) for sorting
        rows = cursor.execute(
            """
            SELECT id, ticker, title, content, agent_name, model_used, created_at
            FROM research_briefs 
            WHERE ticker = ? 
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
            """,
            (ticker_upper, limit, offset)
        ).fetchall()
        
        briefs = [dict(row) for row in rows]
    
    return briefs, total_count
```

--- FILE: backend/core/stock_manager.py ---
```python
#!/usr/bin/env python3
"""
Stock Manager - Handles dynamic stock list management
Optimized for query performance with proper indexing and parameterized queries.
"""

import logging
from typing import List, Dict, Optional

from backend.config import Config
from backend.database import db_session
from backend.core.query_optimizer import (
    get_active_stocks_optimized,
    batch_get_stocks_by_tickers,
)

logger = logging.getLogger(__name__)


def init_stocks_table() -> None:
    """Initialize stocks table in database."""
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Table created by database.py init_all_tables()
        # Just add default stocks if table is empty
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


def get_active_stocks() -> List[str]:
    """Get list of active stock tickers (optimized SQL query)."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT ticker FROM stocks WHERE active = 1 ORDER BY ticker')
        stocks = [row['ticker'] for row in cursor.fetchall()]
    return stocks


def get_all_stocks() -> List[Dict]:
    """Get all active stocks with details (optimized for pagination use)."""
    stocks, _ = get_active_stocks_optimized(market=None, limit=10000, offset=0)
    return stocks


def add_stock(ticker: str, name: str, market: str = 'US') -> bool:
    """Add a new stock to monitor."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            
            ticker = ticker.upper()
            # Auto-detect market based on ticker suffix
            if '.NS' in ticker or '.BO' in ticker:
                market = 'India'
            
            cursor.execute(
                'INSERT OR REPLACE INTO stocks (ticker, name, market, active) VALUES (?, ?, ?, 1)',
                (ticker, name, market)
            )
            logger.info(f"Added stock: {ticker} - {name}")
            return True
    except Exception as e:
        logger.error(f"Error adding stock {ticker}: {e}")
        return False


def remove_stock(ticker: str) -> bool:
    """Remove a stock from monitoring (soft delete)."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            
            ticker = ticker.upper()
            cursor.execute('UPDATE stocks SET active = 0 WHERE ticker = ?', (ticker,))
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
        import yfinance as yf
        
        if not query or len(query.strip()) == 0:
            return []
        
        query_upper = query.upper().strip()
        
        # Try to get ticker info
        ticker_data = yf.Ticker(query_upper)
        if not ticker_data.info:
            return []
        
        # Extract name from ticker info
        name = ticker_data.info.get('longName', query_upper)
        
        return [{'ticker': query_upper, 'name': name}]
    except Exception as e:
        logger.warning(f"Error searching for ticker '{query}': {e}")
        return []


def get_stocks_with_filter(
    market: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[List[Dict], int]:
    """
    Get active stocks with market filtering (SQL-side optimization).
    
    Args:
        market: Optional market filter. If None or 'All', no filter applied.
        limit: Max records to return
        offset: Pagination offset
    
    Returns:
        Tuple of (stocks_list, total_count)
    """
    return get_active_stocks_optimized(market=market, limit=limit, offset=offset)


def get_stock_by_ticker(ticker: str) -> Optional[Dict]:
    """Fetch a single stock by ticker."""
    stocks = batch_get_stocks_by_tickers([ticker.upper()])
    return stocks.get(ticker.upper())
```