```python
"""
TickerPulse AI v3.0 - Flask Application Factory
Creates and configures the Flask app, registers blueprints, sets up SSE/WebSocket,
initialises the database and scheduler.
"""

import json
import queue
import logging
import threading
import secrets
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, Response, jsonify, send_from_directory, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room, disconnect

from backend.config import Config
from backend.database import init_all_tables

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# WebSocket infrastructure
# ---------------------------------------------------------------------------

socketio: SocketIO | None = None
websocket_subscriptions: dict[str, set[str]] = {}  # {ticker: {sid1, sid2, ...}}
websocket_lock = threading.Lock()


def broadcast_price_update(ticker: str, price_data: dict) -> None:
    """Broadcast a price update to all clients subscribed to a ticker.
    
    Args:
        ticker: Stock ticker symbol
        price_data: Price update data (e.g. {'price': 125.50, 'timestamp': '...'})
    """
    if not socketio:
        return
    
    with websocket_lock:
        if ticker in websocket_subscriptions:
            room = f"ticker_{ticker}"
            socketio.emit(
                'price_update',
                {
                    'ticker': ticker,
                    **price_data
                },
                room=room,
                namespace='/prices'
            )


# ---------------------------------------------------------------------------
# SSE (Server-Sent Events) infrastructure -- simple queue-based, no Redis
# ---------------------------------------------------------------------------

sse_clients: list[queue.Queue] = []
sse_lock = threading.Lock()


def send_sse_event(event_type: str, data: dict) -> None:
    """Push an event to every connected SSE client."""
    with sse_lock:
        dead_clients: list[queue.Queue] = []
        for client_queue in sse_clients:
            try:
                client_queue.put_nowait((event_type, data))
            except queue.Full:
                dead_clients.append(client_queue)
        # Remove any clients whose queues overflowed
        for dead in dead_clients:
            sse_clients.remove(dead)


# ---------------------------------------------------------------------------
# CSRF Token Management (TP-C05)
# ---------------------------------------------------------------------------

CSRF_TOKEN_LENGTH = 32
CSRF_HEADER_NAME = 'X-CSRF-Token'
CSRF_PARAM_NAME = '_csrf_token'
CSRF_SAFE_METHODS = {'GET', 'HEAD', 'OPTIONS', 'TRACE'}


def _get_csrf_token() -> str:
    """Get or create CSRF token in session."""
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_urlsafe(CSRF_TOKEN_LENGTH)
    return session['_csrf_token']


def _validate_csrf_token(token: str | None) -> bool:
    """Validate CSRF token from request."""
    if token is None:
        return False
    expected = session.get('_csrf_token')
    if expected is None:
        return False
    return secrets.compare_digest(token, expected)


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> Flask:
    """Build and return a fully configured Flask application."""

    app = Flask(
        __name__,
        static_folder=str(Config.BASE_DIR / 'frontend' / 'build'),
        template_folder=str(Config.BASE_DIR / 'templates'),
    )

    # -- Core Flask config ---------------------------------------------------
    app.config['SECRET_KEY'] = Config.SECRET_KEY
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # -- Logging -------------------------------------------------------------
    _setup_logging(app)

    # -- CORS ----------------------------------------------------------------
    try:
        from flask_cors import CORS
        CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    except ImportError:
        logger.warning(
            "flask-cors is not installed -- CORS headers will NOT be added. "
            "Install with: pip install flask-cors"
        )

    # -- Database ------------------------------------------------------------
    with app.app_context():
        init_all_tables()
        logger.info("Database tables initialised")

    # -- WebSocket/SocketIO --------------------------------------------------
    global socketio
    try:
        socketio = SocketIO(
            app,
            cors_allowed_origins=Config.CORS_ORIGINS,
            async_mode='threading',
            ping_timeout=60,
            ping_interval=25,
        )
        logger.info("SocketIO initialised for WebSocket support")
    except Exception as exc:
        logger.warning("Could not initialise SocketIO: %s. WebSocket disabled.", exc)
        socketio = None

    # -- CSRF Protection Middleware (TP-C05) ---------------------------------
    @app.before_request
    def csrf_protection():
        """Validate CSRF tokens for state-changing operations."""
        if request.method not in CSRF_SAFE_METHODS:
            token = request.headers.get(CSRF_HEADER_NAME) or request.form.get(CSRF_PARAM_NAME)
            if not _validate_csrf_token(token):
                logger.warning(f"CSRF validation failed for {request.method} {request.path}")
                return jsonify({
                    'error': 'CSRF token validation failed',
                    'message': 'Missing or invalid CSRF token'
                }), 403

    # -- Register API blueprints ---------------------------------------------
    _register_blueprints(app)

    # -- CSRF Token Endpoint (TP-C05) ----------------------------------------
    @app.route('/api/csrf-token', methods=['GET', 'POST'])
    def get_csrf_token():
        """Get CSRF token for form submissions and state-changing operations.
        
        Returns:
            JSON object with 'csrf_token' field
            
        Security:
            - Token stored in secure, httponly session cookie
            - Token is unique per session
            - Required for all POST/PUT/DELETE operations
        """
        token = _get_csrf_token()
        return jsonify({'csrf_token': token})

    # -- SSE endpoint --------------------------------------------------------
    @app.route('/api/stream')
    def stream():
        """Server-Sent Events stream for real-time UI updates."""
        def event_stream():
            q: queue.Queue = queue.Queue(maxsize=256)
            with sse_lock:
                sse_clients.append(q)
            try:
                # Send immediate heartbeat so the browser knows we're connected
                yield "event: heartbeat\ndata: {}\n\n"
                while True:
                    try:
                        event_type, data = q.get(timeout=15)
                        yield (
                            f"event: {event_type}\n"
                            f"data: {json.dumps(data)}\n\n"
                        )
                    except queue.Empty:
                        # Send a heartbeat so proxies / browsers don't drop
                        yield "event: heartbeat\ndata: {}\n\n"
            except GeneratorExit:
                pass
            finally:
                with sse_lock:
                    if q in sse_clients:
                        sse_clients.remove(q)

        return Response(
            event_stream(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',  # nginx compatibility
                'Connection': 'keep-alive',
            },
        )

    # -- Health check --------------------------------------------------------
    @app.route('/api/health')
    def health():
        """Simple health-check endpoint for load balancers / monitoring."""
        import sqlite3
        db_status = 'error'
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            conn.execute('SELECT 1')
            conn.close()
            db_status = 'ok'
        except Exception:
            pass

        return jsonify({
            'status': 'ok',
            'version': '3.0.0',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'database': db_status,
        })

    # -- Legacy dashboard fallback -------------------------------------------
    @app.route('/legacy')
    def legacy_dashboard():
        """Serve the original v1/v2 dashboard.html as a fallback."""
        return send_from_directory(
            str(Config.BASE_DIR / 'templates'),
            'dashboard.html',
        )

    # -- APScheduler ---------------------------------------------------------
    _init_scheduler(app)

    return app


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _setup_logging(app: Flask) -> None:
    """Configure application-wide logging with rotating file handler."""
    log_dir = Path(Config.LOG_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)

    # Rotating file handler
    file_handler = RotatingFileHandler(
        str(log_dir / 'tickerpulse.log'),
        maxBytes=Config.LOG_MAX_BYTES,
        backupCount=Config.LOG_BACKUP_COUNT,
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))

    # Apply to root logger so all modules pick it up
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    app.logger.setLevel(log_level)


def _register_blueprints(app: Flask) -> None:
    """Import and register API blueprints.

    Each blueprint lives in ``backend/api/<module>.py`` and exposes a
    Flask ``Blueprint`` instance named ``<name>_bp``.  Missing modules
    are logged as warnings so the app can still start during incremental
    development.
    """
    blueprint_map = {
        'backend.api.stocks':           'stocks_bp',
        'backend.api.news':             'news_bp',
        'backend.api.analysis':         'analysis_bp',
        'backend.api.agents':           'agents_bp',
        'backend.api.research':         'research_bp',
        'backend.api.chat':             'chat_bp',
        'backend.api.settings':         'settings_bp',
        'backend.api.scheduler_routes': 'scheduler_bp',
        'backend.api.downloads':        'bp',
        'backend.api.prices':           'prices_bp',
    }

    for module_path, bp_name in blueprint_map.items():
        try:
            module = __import__(module_path, fromlist=[bp_name])
            bp = getattr(module, bp_name)
            app.register_blueprint(bp)
            logger.info("Registered blueprint: %s from %s", bp_name, module_path)
        except (ImportError, AttributeError) as exc:
            logger.warning(
                "Could not register blueprint %s from %s -- %s. "
                "The module may not exist yet; skipping.",
                bp_name, module_path, exc,
            )


def _init_scheduler(app: Flask) -> None:
    """Initialise APScheduler and register all scheduled jobs."""
    try:
        from flask_apscheduler import APScheduler

        app.config['SCHEDULER_API_ENABLED'] = Config.SCHEDULER_API_ENABLED
        app.config['SCHEDULER_API_PREFIX'] = Config.SCHEDULER_API_PREFIX

        scheduler = APScheduler()
        scheduler.init_app(app)

        # Attach to app so backend.scheduler can access it later
        app.scheduler = scheduler
        logger.info("APScheduler initialised")
    except ImportError:
        logger.warning(
            "flask-apscheduler is not installed -- scheduler disabled. "
            "Install with: pip install flask-apscheduler"
        )

    # Register all jobs with SchedulerManager so they appear in the UI,
    # regardless of whether APScheduler is running.
    try:
        from backend.scheduler import scheduler_manager
        from backend.jobs import register_all_jobs

        register_all_jobs(scheduler_manager)

        # Initialize with the app (connects to APScheduler if available)
        if hasattr(app, 'scheduler'):
            scheduler_manager.init_app(app)
            scheduler_manager.start_all_jobs()
            logger.info("SchedulerManager connected to APScheduler, jobs started")

        logger.info("Registered %d scheduled jobs", len(scheduler_manager._job_registry))
    except Exception as exc:
        logger.warning("Could not register scheduled jobs: %s", exc)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    application = create_app()
    if socketio:
        socketio.run(
            application,
            host='0.0.0.0',
            port=Config.FLASK_PORT,
            debug=Config.FLASK_DEBUG,
            allow_unsafe_werkzeug=True,
        )
    else:
        application.run(
            host='0.0.0.0',
            port=Config.FLASK_PORT,
            debug=Config.FLASK_DEBUG,
        )
```