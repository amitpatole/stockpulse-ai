"""
Earnings calendar refresh job.

Schedule: Daily at 6:00 AM ET
Fetches upcoming earnings dates for all active watchlist stocks from yfinance
and upserts them into the earnings_events table.
"""
import logging
import math
import sqlite3
from datetime import datetime, timezone

import yfinance as yf

from backend.config import Config
from backend.jobs._helpers import job_timer

logger = logging.getLogger(__name__)

JOB_ID = 'earnings_refresh'
JOB_NAME = 'Earnings Refresh'


def run_earnings_refresh() -> None:
    """Fetch upcoming earnings for all active stocks and upsert into earnings_events.

    For each active stock in the watchlist, queries yfinance for the next
    earnings date and EPS estimate, then upserts a row into earnings_events.
    Inactive stocks, tickers with no calendar data, and any yfinance errors are
    skipped without aborting the job.
    """
    with job_timer(JOB_ID, JOB_NAME) as ctx:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            stocks = conn.execute(
                "SELECT ticker FROM stocks WHERE active = 1"
            ).fetchall()
        finally:
            conn.close()

        if not stocks:
            ctx['result_summary'] = 'No active stocks — skipping earnings refresh.'
            return

        fetched_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
        inserted = 0
        skipped = 0

        for stock in stocks:
            ticker = stock['ticker']
            try:
                yf_ticker = yf.Ticker(ticker)
                calendar = yf_ticker.calendar

                if calendar is None:
                    skipped += 1
                    continue

                # calendar is a dict (mock or older yfinance) or a DataFrame
                if hasattr(calendar, 'get'):
                    earnings_dates = calendar.get('Earnings Date') or []
                    eps_raw = calendar.get('EPS Estimate')
                else:
                    skipped += 1
                    continue

                if not earnings_dates:
                    skipped += 1
                    continue

                earnings_date_str = str(earnings_dates[0])[:10]

                eps_estimate: float | None = None
                if eps_raw is not None:
                    try:
                        val = float(eps_raw)
                        if not math.isnan(val):
                            eps_estimate = val
                    except (TypeError, ValueError):
                        pass

                company: str | None = None
                try:
                    info = yf_ticker.info
                    if info:
                        company = info.get('longName')
                except Exception:
                    pass

                conn = sqlite3.connect(Config.DB_PATH)
                try:
                    conn.execute(
                        """
                        INSERT INTO earnings_events
                            (ticker, company, earnings_date, eps_estimate, fetched_at)
                        VALUES (?, ?, ?, ?, ?)
                        ON CONFLICT(ticker, earnings_date) DO UPDATE SET
                            company      = excluded.company,
                            eps_estimate = excluded.eps_estimate,
                            fetched_at   = excluded.fetched_at
                        """,
                        (ticker, company, earnings_date_str, eps_estimate, fetched_at),
                    )
                    conn.commit()
                    inserted += 1
                finally:
                    conn.close()

            except Exception as exc:
                logger.warning("earnings_refresh: error processing %s: %s", ticker, exc)
                skipped += 1

        ctx['result_summary'] = (
            f"Earnings refresh complete: {inserted} upserted, {skipped} skipped."
        )
