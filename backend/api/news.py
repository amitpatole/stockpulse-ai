"""
TickerPulse AI v3.0 - News API Routes
Blueprint for news articles, alerts, and statistics endpoints.
"""

from flask import Blueprint, jsonify, request
import logging

from backend.database import get_db_connection

logger = logging.getLogger(__name__)

news_bp = Blueprint('news', __name__, url_prefix='/api')


@news_bp.route('/news', methods=['GET'])
def get_news():
    """Get recent news articles with optional ticker filter.

    Query Parameters:
        ticker (str, optional): Filter articles by stock ticker.

    Returns:
        JSON array of news article objects. Limited to 50 per ticker or 100 overall.
    """
    ticker = request.args.get('ticker', None)

    conn = get_db_connection()
    cursor = conn.cursor()

    if ticker:
        cursor.execute('''
            SELECT * FROM news
            WHERE ticker = ?
            ORDER BY created_at DESC
            LIMIT 50
        ''', (ticker,))
    else:
        cursor.execute('''
            SELECT * FROM news
            ORDER BY created_at DESC
            LIMIT 100
        ''')

    news = cursor.fetchall()
    conn.close()

    return jsonify([{
        'id': article['id'],
        'ticker': article['ticker'],
        'title': article['title'],
        'description': article['description'],
        'url': article['url'],
        'source': article['source'],
        'published_date': article['published_date'],
        'sentiment_score': article['sentiment_score'],
        'sentiment_label': article['sentiment_label'],
        'created_at': article['created_at']
    } for article in news])


@news_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """Get recent alerts (last 50).

    Returns:
        JSON array of alert objects joined with their associated news articles.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT a.*, n.title, n.url, n.source, n.sentiment_score
        FROM alerts a
        LEFT JOIN news n ON a.news_id = n.id
        ORDER BY a.created_at DESC
        LIMIT 50
    ''')

    alerts = cursor.fetchall()
    conn.close()

    return jsonify([{
        'id': alert['id'],
        'ticker': alert['ticker'],
        'alert_type': alert['alert_type'],
        'message': alert['message'],
        'created_at': alert['created_at'],
        'title': alert['title'],
        'url': alert['url'],
        'source': alert['source'],
        'sentiment_score': alert['sentiment_score']
    } for alert in alerts])


@news_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get sentiment statistics for the last 24 hours.

    Query Parameters:
        market (str, optional): Filter by market. 'All' or omitted returns all markets.

    Returns:
        JSON object with 'stocks' array (per-ticker stats) and 'total_alerts_24h' count.
    """
    market = request.args.get('market', None)
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get stats for each stock with market filter
    if market and market != 'All':
        cursor.execute('''
            SELECT
                n.ticker,
                COUNT(*) as total_articles,
                SUM(CASE WHEN n.sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN n.sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
                SUM(CASE WHEN n.sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
                AVG(n.sentiment_score) as avg_sentiment
            FROM news n
            INNER JOIN stocks s ON n.ticker = s.ticker
            WHERE n.created_at > datetime('now', '-24 hours')
                AND s.market = ?
            GROUP BY n.ticker
        ''', (market,))
    else:
        cursor.execute('''
            SELECT
                ticker,
                COUNT(*) as total_articles,
                SUM(CASE WHEN sentiment_label = 'positive' THEN 1 ELSE 0 END) as positive_count,
                SUM(CASE WHEN sentiment_label = 'negative' THEN 1 ELSE 0 END) as negative_count,
                SUM(CASE WHEN sentiment_label = 'neutral' THEN 1 ELSE 0 END) as neutral_count,
                AVG(sentiment_score) as avg_sentiment
            FROM news
            WHERE created_at > datetime('now', '-24 hours')
            GROUP BY ticker
        ''')

    stats = cursor.fetchall()

    # Get total alerts count
    cursor.execute('SELECT COUNT(*) as count FROM alerts WHERE created_at > datetime("now", "-24 hours")')
    alert_count = cursor.fetchone()['count']

    conn.close()

    return jsonify({
        'stocks': [{
            'ticker': stat['ticker'],
            'total_articles': stat['total_articles'],
            'positive_count': stat['positive_count'],
            'negative_count': stat['negative_count'],
            'neutral_count': stat['neutral_count'],
            'avg_sentiment': round(stat['avg_sentiment'], 2) if stat['avg_sentiment'] else 0
        } for stat in stats],
        'total_alerts_24h': alert_count
    })
