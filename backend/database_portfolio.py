# Add this section to your existing database.py initialization

import aiosqlite
import logging

logger = logging.getLogger(__name__)

async def init_portfolio_tables(db: aiosqlite.Connection) -> None:
    """Initialize portfolio and position tables with proper indexes."""
    
    # Portfolio table: containers for positions
    await db.execute("""
        CREATE TABLE IF NOT EXISTS portfolios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Portfolio positions: tracks individual holdings
    await db.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            quantity REAL NOT NULL CHECK(quantity > 0),
            cost_basis REAL NOT NULL CHECK(cost_basis > 0),
            entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) ON DELETE CASCADE,
            FOREIGN KEY (ticker) REFERENCES stocks(ticker) ON DELETE RESTRICT
        )
    """)
    
    # Indexes for common query patterns (prevents N+1 queries)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_portfolios_created 
        ON portfolios(created_at DESC)
    """)
    
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_portfolio_positions_portfolio 
        ON portfolio_positions(portfolio_id)
    """)
    
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_portfolio_positions_ticker 
        ON portfolio_positions(ticker)
    """)
    
    await db.commit()
    logger.info("Portfolio tables initialized successfully")

async def get_portfolio_with_positions(
    db: aiosqlite.Connection,
    portfolio_id: int
) -> dict[str, any] | None:
    """Fetch portfolio and all positions in single query (avoid N+1)."""
    
    cursor = await db.execute(
        "SELECT id, name, description, created_at, updated_at FROM portfolios WHERE id = ?",
        (portfolio_id,)
    )
    portfolio_row = await cursor.fetchone()
    
    if not portfolio_row:
        return None
    
    cursor = await db.execute(
        """SELECT id, ticker, quantity, cost_basis, entry_date, updated_at 
           FROM portfolio_positions WHERE portfolio_id = ?""",
        (portfolio_id,)
    )
    positions = await cursor.fetchall()
    
    return {
        "portfolio": dict(portfolio_row),
        "positions": [dict(p) for p in positions] if positions else []
    }