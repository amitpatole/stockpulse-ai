```python
"""
TickerPulse AI v3.0 - Flask Application Factory
Creates and configures the Flask app, registers blueprints, sets up SSE,
initialises the database and scheduler.
"""

import json
import queue
import logging
import threading
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask, Response, jsonify, send_from_directory

from backend.config import Config
from backend.database import init_all_tables, get_adapter

logger = logging.getLogger(__name__)


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

    # -- Register API blueprints ---------------------------------------------
    _register_blueprints(app)

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
                        # Heartbeat every 15 seconds
                        yield "event: heartbeat\ndata: {}\n\n"
            finally:
                with sse_lock:
                    sse_clients.remove(q)

        return Response(event_stream(), mimetype='text/event-stream')

    return app


def _setup_logging(app: Flask) -> None:
    """Configure logging for the Flask app."""
    log_dir = Config.BASE_DIR / 'logs'
    log_dir.mkdir(exist_ok=True)

    handler = RotatingFileHandler(
        log_dir / 'app.log',
        maxBytes=10_000_000,  # 10 MB
        backupCount=5,
    )
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    )

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # Reduce noisy libraries
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('apscheduler').setLevel(logging.WARNING)


def _register_blueprints(app: Flask) -> None:
    """Register all API blueprints."""
    # Import blueprints
    from backend.api.stocks import bp as stocks_bp
    from backend.api.news import bp as news_bp
    from backend.api.alerts import bp as alerts_bp
    from backend.api.settings import bp as settings_bp
    from backend.api.providers import bp as providers_bp
    from backend.api.agents import bp as agents_bp
    from backend.api.cost import bp as cost_bp
    from backend.api.research import bp as research_bp
    from backend.api.ratings import bp as ratings_bp
    from backend.api.crypto import bp as crypto_bp
    from backend.api.economic_calendar import bp as economic_calendar_bp
    from backend.api.health import bp as health_bp
    from backend.api.backups import bp as backups_bp

    # Register each blueprint
    app.register_blueprint(stocks_bp, url_prefix='/api/stocks')
    app.register_blueprint(news_bp, url_prefix='/api/news')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(providers_bp, url_prefix='/api/providers')
    app.register_blueprint(agents_bp, url_prefix='/api/agents')
    app.register_blueprint(cost_bp, url_prefix='/api/cost')
    app.register_blueprint(research_bp, url_prefix='/api/research')
    app.register_blueprint(ratings_bp, url_prefix='/api/ratings')
    app.register_blueprint(crypto_bp, url_prefix='/api/crypto')
    app.register_blueprint(economic_calendar_bp, url_prefix='/api/economic-calendar')
    app.register_blueprint(health_bp, url_prefix='/api/health')
    app.register_blueprint(backups_bp, url_prefix='/api/backups')


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)
```