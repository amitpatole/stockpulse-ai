```python
"""
TickerPulse AI - Insider Manager
Business logic for sentiment calculation, aggregation, and insider data.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from backend.database import db_session

logger = logging.getLogger(__name__)


class InsiderManager:
    """Manages insider trading data, calculations, and queries."""

    @staticmethod
    def add_transaction(
        cik: str,
        ticker: str,
        insider_name: str,
        title: str,
        transaction_type: str,
        shares: int,
        price: float,
        value: float,
        filing_date: datetime,
        transaction_date: datetime,
        sentiment_score: float,
        is_derivative: bool = False,
        filing_url: str = '',
        form4_url: str = '',
    ) -> Optional[int]:
        """Add an insider transaction, or skip if duplicate."""
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO insider_transactions (
                        cik, ticker, insider_name, title, transaction_type,
                        shares, price, value, filing_date, transaction_date,
                        sentiment_score, is_derivative, filing_url, form4_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cik, ticker, insider_name, title, transaction_type,
                    shares, price, value, filing_date, transaction_date,
                    sentiment_score, is_derivative, filing_url, form4_url,
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.warning(f"Failed to add insider transaction: {e}")
            return None

    @staticmethod
    def update_insider_info(cik: str, ticker: str, company_name: str = '') -> None:
        """Create or update insider mapping."""
        try:
            with db_session() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO insiders (cik, ticker, company_name, last_filing_date)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(cik) DO UPDATE SET
                        company_name = COALESCE(?, company_name),
                        last_filing_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                """, (cik, ticker, company_name, datetime.utcnow(),
                      company_name, datetime.utcnow()))
                conn.commit()
        except Exception as e:
            logger.warning(f"Failed to update insider info: {e}")

    @staticmethod
    def list_filings(
        ticker: Optional[str] = None,
        cik: Optional[str] = None,
        transaction_type: Optional[str] = None,
        min_days: int = 30,
        min_sentiment: Optional[float] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """List insider transactions with filtering and pagination."""
        limit = max(1, min(100, limit))
        offset = max(0, offset)

        try:
            with db_session() as conn:
                cursor = conn.cursor()

                # Build query
                where_clauses = []
                params = []

                if ticker:
                    where_clauses.append("ticker = ?")
                    params.append(ticker.upper())

                if cik:
                    where_clauses.append("cik = ?")
                    params.append(cik)

                if transaction_type and transaction_type != 'all':
                    where_clauses.append("transaction_type = ?")
                    params.append(transaction_type)

                if min_days > 0:
                    cutoff = datetime.utcnow() - timedelta(days=min_days)
                    where_clauses.append("filing_date >= ?")
                    params.append(cutoff)

                if min_sentiment is not None:
                    where_clauses.append("sentiment_score >= ?")
                    params.append(min_sentiment)

                where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

                # Get total count
                count_sql = f"SELECT COUNT(*) as cnt FROM insider_transactions WHERE {where_sql}"
                total_count = cursor.execute(count_sql, params).fetchone()['cnt']

                # Get paginated results
                query_sql = f"""
                    SELECT id, cik, ticker, insider_name, title, transaction_type,
                           shares, price, value, filing_date, transaction_date,
                           sentiment_score, is_derivative, filing_url, form4_url,
                           created_at
                    FROM insider_transactions
                    WHERE {where_sql}
                    ORDER BY filing_date DESC
                    LIMIT ? OFFSET ?
                """
                params.extend([limit, offset])
                rows = cursor.execute(query_sql, params).fetchall()

                filings = [dict(row) for row in rows]

                return {
                    "data": filings,
                    "meta": {
                        "total_count": total_count,
                        "limit": limit,
                        "offset": offset,
                        "has_next": (offset + limit) < total_count,
                    },
                    "errors": [],
                }
        except Exception as e:
            logger.exception("Error listing insider filings")
            return {
                "data": None,
                "meta": {},
                "errors": [str(e)],
            }

    @staticmethod
    def get_stats(cik: str, ticker: Optional[str] = None, days: int = 30) -> Dict[str, Any]:
        """Get aggregate sentiment and share flow statistics."""
        try:
            with db_session() as conn:
                cursor = conn.cursor()

                cutoff = datetime.utcnow() - timedelta(days=days)

                where_sql = "cik = ? AND filing_date >= ?"
                params = [cik, cutoff]

                if ticker:
                    where_sql += " AND ticker = ?"
                    params.append(ticker.upper())

                # Fetch transactions
                query_sql = f"""
                    SELECT transaction_type, shares, value, sentiment_score, ticker
                    FROM insider_transactions
                    WHERE {where_sql}
                """
                rows = cursor.execute(query_sql, params).fetchall()

                if not rows:
                    return {
                        "data": None,
                        "meta": {},
                        "errors": ["No transactions found for this CIK"],
                    }

                transactions = [dict(row) for row in rows]

                # Calculate aggregates
                net_shares = 0
                buy_count = 0
                sell_count = 0
                total_buy_value = 0.0
                total_sell_value = 0.0
                sentiment_scores = []

                for txn in transactions:
                    txn_type = txn['transaction_type']
                    shares = txn['shares'] or 0
                    value = txn['value'] or 0.0
                    sentiment = txn['sentiment_score'] or 0.0

                    if txn_type == 'purchase':
                        net_shares += shares
                        buy_count += 1
                        total_buy_value += value
                    elif txn_type == 'sale':
                        net_shares -= shares
                        sell_count += 1
                        total_sell_value += value

                    sentiment_scores.append(sentiment)

                sentiment_avg = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0

                # Get last ticker and insider count
                last_ticker = transactions[-1]['ticker'] if transactions else ''
                query_sql = f"SELECT COUNT(DISTINCT insider_name) as cnt FROM insider_transactions WHERE {where_sql}"
                insider_count = cursor.execute(query_sql, params).fetchone()['cnt']

                # Get last filing date
                query_sql = f"SELECT MAX(filing_date) as last_date FROM insider_transactions WHERE {where_sql}"
                last_date_row = cursor.execute(query_sql, params).fetchone()
                last_filing_date = last_date_row['last_date'] if last_date_row['last_date'] else None

                return {
                    "data": {
                        "cik": cik,
                        "ticker": last_ticker,
                        "period_days": days,
                        "net_shares": net_shares,
                        "buy_count": buy_count,
                        "sell_count": sell_count,
                        "total_buy_value": total_buy_value,
                        "total_sell_value": total_sell_value,
                        "sentiment_avg": round(sentiment_avg, 2),
                        "insider_count": insider_count,
                        "last_filing_date": last_filing_date,
                    },
                    "meta": {},
                    "errors": [],
                }
        except Exception as e:
            logger.exception(f"Error getting insider stats for {cik}")
            return {
                "data": None,
                "meta": {},
                "errors": [str(e)],
            }

    @staticmethod
    def get_watchlist_activity(
        tickers: List[str],
        days: int = 7,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """Get insider activity for a list of watchlist tickers."""
        limit = max(1, min(100, limit))
        offset = max(0, offset)

        try:
            if not tickers:
                return {
                    "data": [],
                    "meta": {
                        "total_count": 0,
                        "limit": limit,
                        "offset": offset,
                        "has_next": False,
                    },
                    "errors": [],
                }

            with db_session() as conn:
                cursor = conn.cursor()

                cutoff = datetime.utcnow() - timedelta(days=days)
                placeholders = ','.join('?' * len(tickers))
                ticker_params = [t.upper() for t in tickers]

                # Get total count of tickers with activity
                count_sql = f"""
                    SELECT COUNT(DISTINCT ticker) as cnt
                    FROM insider_transactions
                    WHERE ticker IN ({placeholders}) AND filing_date >= ?
                """
                total_count = cursor.execute(count_sql, ticker_params + [cutoff]).fetchone()['cnt']

                # Get paginated ticker groups
                query_sql = f"""
                    SELECT
                        it.ticker,
                        i.company_name,
                        MAX(it.filing_date) as latest_filing_date,
                        COUNT(*) as transaction_count,
                        AVG(it.sentiment_score) as net_sentiment
                    FROM insider_transactions it
                    LEFT JOIN insiders i ON it.ticker = i.ticker
                    WHERE it.ticker IN ({placeholders}) AND it.filing_date >= ?
                    GROUP BY it.ticker
                    ORDER BY latest_filing_date DESC
                    LIMIT ? OFFSET ?
                """
                rows = cursor.execute(query_sql, ticker_params + [cutoff, limit, offset]).fetchall()

                results = []
                for row in rows:
                    ticker = row['ticker']

                    # Get filings for this ticker
                    filings_sql = f"""
                        SELECT insider_name, transaction_type, shares, sentiment_score
                        FROM insider_transactions
                        WHERE ticker = ? AND filing_date >= ?
                        ORDER BY filing_date DESC
                        LIMIT 10
                    """
                    filings = cursor.execute(filings_sql, [ticker, cutoff]).fetchall()

                    results.append({
                        "ticker": ticker,
                        "company_name": row['company_name'] or '',
                        "latest_filing_date": row['latest_filing_date'],
                        "transaction_count": row['transaction_count'],
                        "filings": [dict(f) for f in filings],
                        "net_sentiment": round(row['net_sentiment'], 2) if row['net_sentiment'] else 0.0,
                    })

                return {
                    "data": results,
                    "meta": {
                        "total_count": total_count,
                        "limit": limit,
                        "offset": offset,
                        "has_next": (offset + limit) < total_count,
                    },
                    "errors": [],
                }
        except Exception as e:
            logger.exception("Error getting watchlist insider activity")
            return {
                "data": None,
                "meta": {},
                "errors": [str(e)],
            }
```