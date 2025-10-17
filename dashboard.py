#!/usr/bin/env python3
"""
StockPulse AI - Real-Time Market Intelligence Dashboard
Web interface for 24/7 stock monitoring with AI-powered analysis
"""

from flask import Flask, render_template, jsonify, request
import sqlite3
from datetime import datetime, timedelta
import json

app = Flask(__name__)
DB_PATH = 'stock_news.db'


def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/status')
def get_status():
    """Get current monitor status"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM monitor_status WHERE id = 1')
    status = cursor.fetchone()

    conn.close()

    if status:
        return jsonify({
            'last_check': status['last_check'],
            'status': status['status'],
            'message': status['message']
        })
    else:
        return jsonify({
            'last_check': None,
            'status': 'not_started',
            'message': 'Monitor has not started yet'
        })


@app.route('/api/alerts')
def get_alerts():
    """Get recent alerts"""
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


@app.route('/api/news')
def get_news():
    """Get recent news articles"""
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


@app.route('/api/stats')
def get_stats():
    """Get statistics"""
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


@app.route('/api/stocks/search')
def search_stocks():
    """Search for stock tickers"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])

    from stock_manager import search_stock_ticker
    results = search_stock_ticker(query)
    return jsonify(results)


@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """Get all monitored stocks"""
    market = request.args.get('market', None)
    from stock_manager import get_all_stocks
    stocks = get_all_stocks()

    # Filter by market if specified
    if market and market != 'All':
        stocks = [s for s in stocks if s.get('market') == market]

    return jsonify(stocks)


@app.route('/api/stocks', methods=['POST'])
def add_stock_endpoint():
    """Add new stock"""
    data = request.json
    from stock_manager import add_stock
    market = data.get('market', 'US')
    success = add_stock(data['ticker'], data['name'], market)
    return jsonify({'success': success})


@app.route('/api/stocks/<ticker>', methods=['DELETE'])
def remove_stock_endpoint(ticker):
    """Remove stock"""
    from stock_manager import remove_stock
    success = remove_stock(ticker)
    return jsonify({'success': success})


@app.route('/api/ai/ratings')
def get_ai_ratings():
    """Get AI ratings for all stocks"""
    from ai_analytics import StockAnalytics
    analytics = StockAnalytics()
    ratings = analytics.get_all_ratings()
    return jsonify(ratings)


@app.route('/api/ai/rating/<ticker>')
def get_ai_rating(ticker):
    """Get AI rating for specific stock"""
    from ai_analytics import StockAnalytics
    analytics = StockAnalytics()
    rating = analytics.calculate_ai_rating(ticker)
    return jsonify(rating)


@app.route('/api/chart/<ticker>')
def get_chart_data(ticker):
    """Get historical price data for chart"""
    period = request.args.get('period', '1mo')
    from ai_analytics import StockAnalytics
    analytics = StockAnalytics()
    price_data = analytics.get_stock_price_data(ticker, period)

    if not price_data or not price_data.get('close'):
        return jsonify({'error': 'No data available'}), 404

    # Filter out None values and prepare data
    timestamps = price_data.get('timestamps', [])
    closes = price_data.get('close', [])
    opens = price_data.get('open', [])
    highs = price_data.get('high', [])
    lows = price_data.get('low', [])
    volumes = price_data.get('volume', [])

    # Create clean data points
    data_points = []
    for i in range(len(timestamps)):
        if closes[i] is not None:
            data_points.append({
                'timestamp': timestamps[i],
                'date': datetime.fromtimestamp(timestamps[i]).strftime('%Y-%m-%d'),
                'open': opens[i],
                'high': highs[i],
                'low': lows[i],
                'close': closes[i],
                'volume': volumes[i]
            })

    if not data_points:
        return jsonify({'error': 'No valid data points'}), 404

    # Calculate price change
    first_price = data_points[0]['close']
    last_price = data_points[-1]['close']
    price_change = last_price - first_price
    price_change_percent = (price_change / first_price) * 100 if first_price else 0

    # Determine currency
    is_indian = '.NS' in ticker.upper() or '.BO' in ticker.upper()
    currency_symbol = '₹' if is_indian else '$'

    return jsonify({
        'ticker': ticker,
        'period': period,
        'data': data_points,
        'currency_symbol': currency_symbol,
        'stats': {
            'current_price': last_price,
            'open_price': first_price,
            'high_price': max([p['high'] for p in data_points if p['high']]),
            'low_price': min([p['low'] for p in data_points if p['low']]),
            'price_change': price_change,
            'price_change_percent': price_change_percent,
            'total_volume': sum([p['volume'] for p in data_points if p['volume']])
        }
    })


# AI Provider Settings Endpoints
@app.route('/api/settings/ai-providers', methods=['GET'])
def get_ai_providers_endpoint():
    """Get all configured AI providers"""
    from settings_manager import get_all_ai_providers
    providers = get_all_ai_providers()
    return jsonify(providers)


@app.route('/api/settings/ai-provider', methods=['POST'])
def add_ai_provider_endpoint():
    """Add or update AI provider"""
    data = request.json
    from settings_manager import add_ai_provider
    success = add_ai_provider(
        data['provider'],
        data['api_key'],
        data.get('model'),
        set_active=True
    )
    return jsonify({'success': success})


@app.route('/api/settings/ai-provider/<int:provider_id>/activate', methods=['POST'])
def activate_ai_provider_endpoint(provider_id):
    """Activate an AI provider"""
    from settings_manager import set_active_provider
    success = set_active_provider(provider_id)
    return jsonify({'success': success})


@app.route('/api/settings/ai-provider/<int:provider_id>', methods=['DELETE'])
def delete_ai_provider_endpoint(provider_id):
    """Delete an AI provider"""
    from settings_manager import delete_ai_provider
    success = delete_ai_provider(provider_id)
    return jsonify({'success': success})


@app.route('/api/settings/test-ai', methods=['POST'])
def test_ai_provider_endpoint():
    """Test AI provider connection"""
    data = request.json
    from ai_providers import test_provider_connection
    result = test_provider_connection(
        data['provider'],
        data['api_key'],
        data.get('model')
    )
    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
