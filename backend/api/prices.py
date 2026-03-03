```python
"""
TickerPulse AI v3.0 - WebSocket Price Streaming API
Real-time ticker price updates via WebSocket (SocketIO).
Subscribes clients to specific tickers and broadcasts price changes.
Implements graceful fallback to REST polling if WebSocket unavailable.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from flask import Blueprint, jsonify, request, session
from flask_socketio import emit, join_room, leave_room, disconnect

from backend.core.stock_manager import get_stock_by_ticker, get_all_stocks
from backend.app import socketio, websocket_subscriptions, websocket_lock

logger = logging.getLogger(__name__)

prices_bp = Blueprint('prices', __name__, url_prefix='/api')


# ---------------------------------------------------------------------------
# REST Fallback Endpoints (for when WebSocket is unavailable)
# ---------------------------------------------------------------------------

@prices_bp.route('/prices/<ticker>', methods=['GET'])
def get_price(ticker: str) -> tuple[Dict[str, Any], int]:
    """Get the current price of a stock (REST fallback).
    
    Used when WebSocket is unavailable. Fetches current price from database.
    
    Args:
        ticker: Stock ticker symbol (e.g. 'AAPL')
    
    Returns:
        JSON object with price data: {price, currency, timestamp, change, change_pct}
        Returns 404 if ticker not found.
    """
    ticker = ticker.upper().strip()
    
    # Validate ticker format (1-5 alphanumeric chars, optional market suffix)
    if not ticker or len(ticker) > 10:
        return jsonify({
            'error': 'Invalid ticker format',
            'message': 'Ticker must be 1-10 characters'
        }), 400
    
    try:
        stock = get_stock_by_ticker(ticker)
        if not stock:
            return jsonify({
                'error': 'Stock not found',
                'message': f'No stock found with ticker {ticker}'
            }), 404
        
        # Return price data from database
        price_data = {
            'ticker': ticker,
            'price': stock.get('current_price', 0),
            'currency': stock.get('currency', 'USD'),
            'timestamp': stock.get('updated_at', datetime.utcnow().isoformat()),
            'change': stock.get('day_change', 0),
            'change_pct': stock.get('day_change_percent', 0),
        }
        
        return jsonify({'data': price_data})
    
    except Exception as exc:
        logger.error(f"Error fetching price for {ticker}: {exc}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Could not fetch price data'
        }), 500


@prices_bp.route('/prices', methods=['GET'])
def get_all_prices() -> tuple[Dict[str, Any], int]:
    """Get prices for all monitored stocks (REST fallback).
    
    Includes pagination support.
    
    Query Parameters:
        limit (int, optional): Max records per page. Default: 50, Max: 200.
        offset (int, optional): Records to skip. Default: 0.
    
    Returns:
        JSON array of price data with pagination metadata.
    """
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
        offset = max(int(request.args.get('offset', 0)), 0)
    except (ValueError, TypeError):
        limit = 50
        offset = 0
    
    try:
        stocks = get_all_stocks()
        
        # Filter active stocks only
        active_stocks = [s for s in stocks if s.get('active', 1) == 1]
        
        # Build price list
        prices = []
        for stock in active_stocks:
            prices.append({
                'ticker': stock.get('ticker'),
                'price': stock.get('current_price', 0),
                'currency': stock.get('currency', 'USD'),
                'timestamp': stock.get('updated_at', datetime.utcnow().isoformat()),
                'change': stock.get('day_change', 0),
                'change_pct': stock.get('day_change_percent', 0),
            })
        
        # Apply pagination
        total_count = len(prices)
        paginated_prices = prices[offset : offset + limit]
        has_next = (offset + limit) < total_count
        has_previous = offset > 0
        
        meta = {
            'total': total_count,
            'limit': limit,
            'offset': offset,
            'has_next': has_next,
            'has_previous': has_previous,
        }
        
        return jsonify({'data': paginated_prices, 'meta': meta})
    
    except Exception as exc:
        logger.error(f"Error fetching all prices: {exc}")
        return jsonify({
            'error': 'Internal server error',
            'message': 'Could not fetch prices'
        }), 500


# ---------------------------------------------------------------------------
# WebSocket Event Handlers (SocketIO namespace: /prices)
# ---------------------------------------------------------------------------

@socketio.on('connect', namespace='/prices')
def handle_connect():
    """Handle WebSocket client connection.
    
    Validates session and logs connection.
    """
    sid = request.sid
    logger.info(f"WebSocket client connected: {sid}")
    emit('connection_response', {
        'status': 'connected',
        'message': 'Connected to price stream',
        'timestamp': datetime.utcnow().isoformat()
    })


@socketio.on('disconnect', namespace='/prices')
def handle_disconnect():
    """Handle WebSocket client disconnection.
    
    Cleans up subscriptions for the disconnected client.
    """
    sid = request.sid
    logger.info(f"WebSocket client disconnected: {sid}")
    
    # Remove client from all subscriptions
    with websocket_lock:
        for ticker in list(websocket_subscriptions.keys()):
            if sid in websocket_subscriptions[ticker]:
                websocket_subscriptions[ticker].remove(sid)
            # Clean up empty ticker subscriptions
            if not websocket_subscriptions[ticker]:
                del websocket_subscriptions[ticker]


@socketio.on('subscribe', namespace='/prices')
def handle_subscribe(data: Dict[str, Any]) -> None:
    """Subscribe client to price updates for a specific ticker.
    
    Args:
        data: {ticker: 'AAPL'} - ticker to subscribe to
    
    Emits:
        subscription_response: Confirms subscription or error
    """
    sid = request.sid
    ticker = data.get('ticker', '').upper().strip() if data else None
    
    # Validate ticker
    if not ticker or len(ticker) > 10:
        emit('subscription_response', {
            'status': 'error',
            'message': 'Invalid ticker format',
            'ticker': ticker
        })
        return
    
    # Check if stock exists
    try:
        stock = get_stock_by_ticker(ticker)
        if not stock:
            emit('subscription_response', {
                'status': 'error',
                'message': f'Stock {ticker} not found',
                'ticker': ticker
            })
            return
    except Exception as exc:
        logger.error(f"Error validating ticker {ticker}: {exc}")
        emit('subscription_response', {
            'status': 'error',
            'message': 'Error validating ticker',
            'ticker': ticker
        })
        return
    
    # Add subscription
    with websocket_lock:
        if ticker not in websocket_subscriptions:
            websocket_subscriptions[ticker] = set()
        websocket_subscriptions[ticker].add(sid)
    
    # Join SocketIO room for this ticker
    room = f"ticker_{ticker}"
    join_room(room, namespace='/prices')
    
    # Confirm subscription
    logger.info(f"Client {sid} subscribed to {ticker}")
    emit('subscription_response', {
        'status': 'subscribed',
        'message': f'Successfully subscribed to {ticker}',
        'ticker': ticker,
        'timestamp': datetime.utcnow().isoformat()
    })


@socketio.on('unsubscribe', namespace='/prices')
def handle_unsubscribe(data: Dict[str, Any]) -> None:
    """Unsubscribe client from price updates for a specific ticker.
    
    Args:
        data: {ticker: 'AAPL'} - ticker to unsubscribe from
    
    Emits:
        unsubscription_response: Confirms unsubscription or error
    """
    sid = request.sid
    ticker = data.get('ticker', '').upper().strip() if data else None
    
    if not ticker:
        emit('unsubscription_response', {
            'status': 'error',
            'message': 'Invalid or missing ticker',
            'ticker': ticker
        })
        return
    
    # Remove subscription
    with websocket_lock:
        if ticker in websocket_subscriptions:
            websocket_subscriptions[ticker].discard(sid)
            if not websocket_subscriptions[ticker]:
                del websocket_subscriptions[ticker]
    
    # Leave SocketIO room
    room = f"ticker_{ticker}"
    leave_room(room, namespace='/prices')
    
    logger.info(f"Client {sid} unsubscribed from {ticker}")
    emit('unsubscription_response', {
        'status': 'unsubscribed',
        'message': f'Successfully unsubscribed from {ticker}',
        'ticker': ticker,
        'timestamp': datetime.utcnow().isoformat()
    })


@socketio.on('get_subscription_status', namespace='/prices')
def handle_get_status() -> None:
    """Get current subscription status for this client.
    
    Emits:
        subscription_status: List of subscribed tickers
    """
    sid = request.sid
    
    subscribed_tickers = []
    with websocket_lock:
        for ticker, sids in websocket_subscriptions.items():
            if sid in sids:
                subscribed_tickers.append(ticker)
    
    emit('subscription_status', {
        'subscriptions': subscribed_tickers,
        'count': len(subscribed_tickers),
        'timestamp': datetime.utcnow().isoformat()
    })


@socketio.on_error_default
def default_error_handler(e):
    """Default error handler for WebSocket events."""
    logger.error(f"WebSocket error: {e}")
    emit('error_response', {
        'status': 'error',
        'message': 'An error occurred processing your request'
    })
```