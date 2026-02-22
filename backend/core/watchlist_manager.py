"""
TickerPulse AI v3.0 - Watchlist Manager
CRUD operations for named watchlist portfolio groups.
"""

import logging
import sqlite3
from typing import List, Dict, Optional

from backend.database import db_session
from backend.core.stock_manager import add_stock, search_stock_ticker

logger = logging.getLogger(__name__)


def get_all_watchlists() -> List[Dict]:
    """Return all watchlists with a stock_count field."""
    with db_session() as conn:
        rows = conn.execute(
            """
            SELECT w.id, w.name, w.created_at,
                   COUNT(ws.ticker) AS stock_count
            FROM watchlists w
            LEFT JOIN watchlist_stocks ws ON ws.watchlist_id = w.id
            GROUP BY w.id
            ORDER BY w.id
            """
        ).fetchall()
    return [dict(r) for r in rows]


def create_watchlist(name: str) -> Dict:
    """Create a new watchlist.  Raises ValueError on duplicate name."""
    name = name.strip()
    if not name:
        raise ValueError("Watchlist name cannot be empty")
    try:
        with db_session() as conn:
            cursor = conn.execute(
                "INSERT INTO watchlists (name) VALUES (?)", (name,)
            )
            wid = cursor.lastrowid
        return {"id": wid, "name": name, "stock_count": 0}
    except sqlite3.IntegrityError:
        raise ValueError(f"Watchlist '{name}' already exists")


def get_watchlist(watchlist_id: int) -> Optional[Dict]:
    """Return a watchlist with its list of tickers, or None if not found."""
    with db_session() as conn:
        row = conn.execute(
            "SELECT id, name, created_at FROM watchlists WHERE id = ?",
            (watchlist_id,),
        ).fetchone()
        if row is None:
            return None
        tickers = [
            r["ticker"]
            for r in conn.execute(
                "SELECT ticker FROM watchlist_stocks"
                " WHERE watchlist_id = ? ORDER BY position, ticker",
                (watchlist_id,),
            ).fetchall()
        ]
    result = dict(row)
    result["tickers"] = tickers
    return result


def rename_watchlist(watchlist_id: int, new_name: str) -> Optional[Dict]:
    """Rename a watchlist. Returns the updated record or None if not found.
    Raises ValueError on duplicate name."""
    new_name = new_name.strip()
    if not new_name:
        raise ValueError("Watchlist name cannot be empty")
    try:
        with db_session() as conn:
            result = conn.execute(
                "UPDATE watchlists SET name = ? WHERE id = ?",
                (new_name, watchlist_id),
            )
            if result.rowcount == 0:
                return None
            row = conn.execute(
                "SELECT id, name, created_at FROM watchlists WHERE id = ?",
                (watchlist_id,),
            ).fetchone()
        return dict(row)
    except sqlite3.IntegrityError:
        raise ValueError(f"Watchlist '{new_name}' already exists")


def delete_watchlist(watchlist_id: int) -> bool:
    """Delete a watchlist. Raises ValueError if it is the last one.
    Returns False if not found, True on success."""
    with db_session() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM watchlists"
        ).fetchone()[0]
        if count <= 1:
            raise ValueError("Cannot delete the last watchlist")
        result = conn.execute(
            "DELETE FROM watchlists WHERE id = ?", (watchlist_id,)
        )
    return result.rowcount > 0


def add_stock_to_watchlist(watchlist_id: int, ticker: str, name: Optional[str] = None) -> bool:
    """Add a ticker to a watchlist.

    Upserts the ticker into the stocks table (if absent) then inserts the
    junction row at the end of the current order.  Returns True on success,
    False if the watchlist does not exist.
    """
    ticker = ticker.strip().upper()

    # Ensure the stock exists in the stocks table
    with db_session() as conn:
        existing = conn.execute(
            "SELECT ticker FROM stocks WHERE ticker = ?", (ticker,)
        ).fetchone()

    if not existing:
        resolved_name = name
        if not resolved_name:
            results = search_stock_ticker(ticker)
            match = next((r for r in results if r["ticker"].upper() == ticker), None)
            resolved_name = match["name"] if match else ticker
        market = "India" if (".NS" in ticker or ".BO" in ticker) else "US"
        add_stock(ticker, resolved_name, market)

    try:
        with db_session() as conn:
            # Verify watchlist exists
            wl = conn.execute(
                "SELECT id FROM watchlists WHERE id = ?", (watchlist_id,)
            ).fetchone()
            if wl is None:
                return False
            next_pos = conn.execute(
                "SELECT COALESCE(MAX(position), -1) + 1"
                " FROM watchlist_stocks WHERE watchlist_id = ?",
                (watchlist_id,),
            ).fetchone()[0]
            conn.execute(
                "INSERT OR IGNORE INTO watchlist_stocks"
                " (watchlist_id, ticker, position) VALUES (?, ?, ?)",
                (watchlist_id, ticker, next_pos),
            )
        # Invalidate stale cache so next ratings fetch recomputes fresh
        with db_session() as conn:
            conn.execute("DELETE FROM ai_ratings WHERE ticker = ?", (ticker,))
        return True
    except Exception as exc:
        logger.error("Error adding %s to watchlist %d: %s", ticker, watchlist_id, exc)
        return False


def reorder_stocks(watchlist_id: int, tickers: List[str]) -> bool:
    """Atomically rewrite positions for all stocks in a watchlist.

    Parameters
    ----------
    watchlist_id : int
        The watchlist whose stocks should be reordered.
    tickers : list[str]
        Ticker symbols in the desired display order (position 0, 1, 2 ...).
        Every ticker currently in the watchlist must be included — no more,
        no less.

    Returns
    -------
    bool
        True on success, False if the watchlist does not exist.

    Raises
    ------
    ValueError
        If the provided ticker list does not exactly match the watchlist's
        current set of tickers.
    """
    with db_session() as conn:
        wl = conn.execute(
            "SELECT id FROM watchlists WHERE id = ?", (watchlist_id,)
        ).fetchone()
        if wl is None:
            return False

        existing = {
            r["ticker"]
            for r in conn.execute(
                "SELECT ticker FROM watchlist_stocks WHERE watchlist_id = ?",
                (watchlist_id,),
            ).fetchall()
        }
        if set(tickers) != existing:
            raise ValueError("Ticker list does not match watchlist contents exactly")

        for idx, ticker in enumerate(tickers):
            conn.execute(
                "UPDATE watchlist_stocks SET position = ?"
                " WHERE watchlist_id = ? AND ticker = ?",
                (idx, watchlist_id, ticker),
            )

    return True


def remove_stock_from_watchlist(watchlist_id: int, ticker: str) -> bool:
    """Remove a ticker from a watchlist (junction row only).
    Returns True if a row was deleted, False otherwise."""
    ticker = ticker.strip().upper()
    with db_session() as conn:
        result = conn.execute(
            "DELETE FROM watchlist_stocks WHERE watchlist_id = ? AND ticker = ?",
            (watchlist_id, ticker),
        )
    # Invalidate stale cache so next ratings fetch recomputes fresh
    with db_session() as conn:
        conn.execute("DELETE FROM ai_ratings WHERE ticker = ?", (ticker,))
    return result.rowcount > 0
