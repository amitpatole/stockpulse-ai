"""
TickerPulse AI v3.0 - Stocks API Routes
Blueprint for stock management endpoints: list, add, remove, and search stocks.
"""

from flask import Blueprint, jsonify, request
import logging

from backend.core.stock_manager import get_all_stocks, add_stock, remove_stock, search_stock_ticker

logger = logging.getLogger(__name__)

stocks_bp = Blueprint('stocks', __name__, url_prefix='/api')


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
        name (str, optional): Company name. Auto-looked up via Yahoo Finance if omitted.
        market (str, optional): Market identifier, defaults to 'US'

    Returns:
        JSON object with 'success' boolean.
    """
    data = request.json
    if not data or 'ticker' not in data:
        return jsonify({'success': False, 'error': 'Missing required field: ticker'}), 400

    ticker = data['ticker'].strip().upper()
    name = data.get('name')

    # Auto-lookup name if not provided
    if not name:
        results = search_stock_ticker(ticker)
        if results:
            name = results[0].get('name', ticker)
        else:
            name = ticker

    market = data.get('market', 'US')
    success = add_stock(ticker, name, market)
    return jsonify({'success': success})


@stocks_bp.route('/stocks/<ticker>', methods=['DELETE'])
def remove_stock_endpoint(ticker):
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
