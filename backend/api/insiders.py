```python
"""
TickerPulse AI - Insider Trading API
Endpoints for listing filings, viewing stats, and watchlist activity.
"""

import logging
from flask import Blueprint, request, jsonify
from backend.core.insider_manager import InsiderManager
from backend.core.stock_manager import StockManager

logger = logging.getLogger(__name__)

insiders_bp = Blueprint("insiders", __name__, url_prefix="/api/insiders")


@insiders_bp.route("/filings", methods=["GET"])
def list_filings():
    """List insider transactions with filtering and pagination.
    
    Query Parameters:
    - ticker: str (optional) - Filter by ticker
    - cik: str (optional) - Filter by CIK
    - type: str (default: all) - Filter by transaction type
    - min_days: int (default: 30) - Look back period
    - min_sentiment: float (optional) - Minimum sentiment score
    - limit: int (default: 50, max: 100)
    - offset: int (default: 0)
    """
    try:
        ticker = request.args.get("ticker", "").upper()
        cik = request.args.get("cik", "")
        txn_type = request.args.get("type", "all")
        min_days = int(request.args.get("min_days", 30))
        min_sentiment = request.args.get("min_sentiment")
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        # Validate ticker exists if provided
        if ticker:
            stock = StockManager.get_stock(ticker)
            if not stock:
                return jsonify({
                    "data": None,
                    "meta": {},
                    "errors": [f"Ticker {ticker} not found"],
                }), 404

        # Parse sentiment filter
        min_sentiment_float = None
        if min_sentiment:
            try:
                min_sentiment_float = float(min_sentiment)
                min_sentiment_float = max(-1.0, min(1.0, min_sentiment_float))
            except ValueError:
                return jsonify({
                    "data": None,
                    "meta": {},
                    "errors": ["min_sentiment must be a float between -1 and 1"],
                }), 400

        # Validate inputs
        if limit < 1 or limit > 100:
            limit = 50
        if offset < 0:
            offset = 0
        if min_days < 0:
            min_days = 30

        result = InsiderManager.list_filings(
            ticker=ticker if ticker else None,
            cik=cik if cik else None,
            transaction_type=txn_type,
            min_days=min_days,
            min_sentiment=min_sentiment_float,
            limit=limit,
            offset=offset,
        )

        return jsonify(result), 200
    except ValueError as e:
        logger.warning(f"Invalid query parameters: {e}")
        return jsonify({
            "data": None,
            "meta": {},
            "errors": [f"Invalid query parameters: {str(e)}"],
        }), 400
    except Exception as e:
        logger.exception("Error listing insider filings")
        return jsonify({
            "data": None,
            "meta": {},
            "errors": [str(e)],
        }), 500


@insiders_bp.route("/<cik>/stats", methods=["GET"])
def get_stats(cik: str):
    """Get aggregate sentiment and share flow statistics.
    
    Path Parameters:
    - cik: str - SEC Central Index Key
    
    Query Parameters:
    - days: int (default: 30, choices: 7|30|90)
    - ticker: str (optional) - Filter to specific ticker
    """
    try:
        ticker = request.args.get("ticker", "").upper()
        days = int(request.args.get("days", 30))

        # Validate days parameter
        if days not in (7, 30, 90):
            return jsonify({
                "data": None,
                "meta": {},
                "errors": ["days must be 7, 30, or 90"],
            }), 400

        # Validate ticker if provided
        if ticker:
            stock = StockManager.get_stock(ticker)
            if not stock:
                return jsonify({
                    "data": None,
                    "meta": {},
                    "errors": [f"Ticker {ticker} not found"],
                }), 404

        result = InsiderManager.get_stats(
            cik=cik,
            ticker=ticker if ticker else None,
            days=days,
        )

        # Check if data found
        if result["data"] is None:
            return jsonify(result), 404

        return jsonify(result), 200
    except ValueError as e:
        logger.warning(f"Invalid query parameters: {e}")
        return jsonify({
            "data": None,
            "meta": {},
            "errors": [f"Invalid query parameters: {str(e)}"],
        }), 400
    except Exception as e:
        logger.exception(f"Error getting insider stats for {cik}")
        return jsonify({
            "data": None,
            "meta": {},
            "errors": [str(e)],
        }), 500


@insiders_bp.route("/watchlist/activity", methods=["GET"])
def get_watchlist_activity():
    """Get insider activity for watchlist stocks.
    
    Query Parameters:
    - tickers: str (comma-separated) - Stock tickers to filter
    - days: int (default: 7) - Look back period
    - limit: int (default: 50, max: 100)
    - offset: int (default: 0)
    """
    try:
        tickers_param = request.args.get("tickers", "")
        days = int(request.args.get("days", 7))
        limit = int(request.args.get("limit", 50))
        offset = int(request.args.get("offset", 0))

        # Parse tickers
        tickers = [t.strip().upper() for t in tickers_param.split(",") if t.strip()]

        # Validate inputs
        if limit < 1 or limit > 100:
            limit = 50
        if offset < 0:
            offset = 0
        if days < 1:
            days = 7

        result = InsiderManager.get_watchlist_activity(
            tickers=tickers,
            days=days,
            limit=limit,
            offset=offset,
        )

        return jsonify(result), 200
    except ValueError as e:
        logger.warning(f"Invalid query parameters: {e}")
        return jsonify({
            "data": None,
            "meta": {},
            "errors": [f"Invalid query parameters: {str(e)}"],
        }), 400
    except Exception as e:
        logger.exception("Error getting watchlist insider activity")
        return jsonify({
            "data": None,
            "meta": {},
            "errors": [str(e)],
        }), 500
```