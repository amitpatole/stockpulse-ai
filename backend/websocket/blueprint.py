"""
WebSocket Flask Blueprint - Integration with SocketIO for event handling.
Provides the blueprint factory for tests and event handler registration.
"""

import logging
from flask import Blueprint

logger = logging.getLogger(__name__)


def create_websocket_blueprint() -> Blueprint:
    """Create a Flask Blueprint for WebSocket routes.

    This blueprint provides a placeholder health check endpoint for WebSocket
    diagnostics. Actual WebSocket events are handled by SocketIO event handlers
    registered in the app factory.

    Returns
    -------
    Blueprint
        Flask blueprint for WebSocket routes.
    """
    bp = Blueprint('websocket', __name__, url_prefix='/api/websocket')

    @bp.route('/health', methods=['GET'])
    def websocket_health():
        """Check WebSocket server health.

        Returns
        -------
        dict
            Status response with connection count (if SocketIO available).
        """
        from flask import jsonify
        try:
            from backend.app import socketio
            if socketio is None:
                return jsonify({
                    'status': 'error',
                    'message': 'WebSocket not initialized'
                }), 503

            return jsonify({
                'status': 'ok',
                'message': 'WebSocket server is running'
            })
        except Exception as e:
            logger.error(f"Error checking WebSocket health: {e}")
            return jsonify({
                'status': 'error',
                'message': 'WebSocket health check failed'
            }), 500

    return bp


def register_websocket_events(socketio):
    """Register SocketIO event handlers with the app's SocketIO instance.

    This function is called by the app factory to set up WebSocket event
    handlers for subscribe, unsubscribe, and message handling.

    Parameters
    ----------
    socketio : SocketIO
        The SocketIO instance from flask_socketio.
    """
    logger.info("Registering WebSocket event handlers")

    @socketio.on('connect', namespace='/prices')
    def handle_connect():
        """Handle client connection to /prices namespace.

        The client should be authenticated (checked via session).
        """
        from flask import session, request
        logger.info(f"Client connected to /prices: {request.sid}")

        # Optionally check authentication here
        # if 'user_id' not in session:
        #     return False

    @socketio.on('disconnect', namespace='/prices')
    def handle_disconnect():
        """Handle client disconnection from /prices namespace."""
        from flask import request
        logger.info(f"Client disconnected from /prices: {request.sid}")

    @socketio.on('subscribe', namespace='/prices')
    def handle_subscribe(data):
        """Handle ticker subscription request.

        Expected message format:
        {
            "tickers": ["AAPL", "MSFT", "GOOGL"]
        }

        Parameters
        ----------
        data : dict
            Subscription request data.
        """
        from flask import request

        if not isinstance(data, dict):
            return {'error': 'Invalid message format'}

        tickers = data.get('tickers', [])
        if not isinstance(tickers, list):
            return {'error': 'tickers must be a list'}

        # Import here to avoid circular imports
        from backend.app import websocket_subscriptions, websocket_lock

        with websocket_lock:
            for ticker in tickers:
                ticker_upper = ticker.upper()
                if ticker_upper not in websocket_subscriptions:
                    websocket_subscriptions[ticker_upper] = set()
                websocket_subscriptions[ticker_upper].add(request.sid)

        logger.info(f"Client {request.sid} subscribed to {tickers}")
        return {'subscribed': [t.upper() for t in tickers]}

    @socketio.on('unsubscribe', namespace='/prices')
    def handle_unsubscribe(data):
        """Handle ticker unsubscription request.

        Expected message format:
        {
            "tickers": ["AAPL", "MSFT"]
        }

        Parameters
        ----------
        data : dict
            Unsubscription request data.
        """
        from flask import request

        if not isinstance(data, dict):
            return {'error': 'Invalid message format'}

        tickers = data.get('tickers', [])
        if not isinstance(tickers, list):
            return {'error': 'tickers must be a list'}

        # Import here to avoid circular imports
        from backend.app import websocket_subscriptions, websocket_lock

        with websocket_lock:
            for ticker in tickers:
                ticker_upper = ticker.upper()
                if ticker_upper in websocket_subscriptions:
                    websocket_subscriptions[ticker_upper].discard(request.sid)

        logger.info(f"Client {request.sid} unsubscribed from {tickers}")
        return {'unsubscribed': [t.upper() for t in tickers]}

    @socketio.on('ping', namespace='/prices')
    def handle_ping():
        """Handle ping/pong heartbeat."""
        from datetime import datetime, timezone
        return {
            'type': 'pong',
            'timestamp': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }

    logger.info("WebSocket event handlers registered")
