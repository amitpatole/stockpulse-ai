#!/usr/bin/env python3
"""
Stock News Monitor - Tracks news for specified stocks and alerts on positive sentiment
"""

import time
import sqlite3
import requests
import feedparser
from datetime import datetime, timedelta
import json
import re
from typing import List, Dict, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Stocks to monitor
STOCKS = ['GTI', 'APLD', 'INTC', 'USAR', 'CRML', 'NVTS', 'OKLO', 'HUT', 'IBIT', 'CGC']

# News check interval (in seconds) - 5 minutes
CHECK_INTERVAL = 300

# Positive and negative keywords for sentiment analysis
POSITIVE_KEYWORDS = [
    'surge', 'soar', 'rally', 'gain', 'rise', 'jump', 'climb', 'boost', 'upgrade',
    'bullish', 'positive', 'growth', 'profit', 'revenue', 'beat', 'exceed', 'outperform',
    'strong', 'robust', 'expansion', 'breakthrough', 'partnership', 'deal', 'acquisition',
    'innovation', 'success', 'award', 'win', 'record', 'high', 'optimistic', 'momentum',
    'buy', 'overweight', 'increased guidance', 'raised guidance', 'dividend increase'
]

NEGATIVE_KEYWORDS = [
    'plunge', 'crash', 'drop', 'fall', 'decline', 'loss', 'bearish', 'negative',
    'downgrade', 'sell', 'underperform', 'weak', 'concern', 'warning', 'miss',
    'below', 'disappointed', 'cut', 'reduced guidance', 'lowered guidance', 'lawsuit',
    'investigation', 'fraud', 'scandal', 'bankrupt', 'debt', 'trouble'
]


class StockNewsMonitor:
    def __init__(self, db_path='stock_news.db'):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT UNIQUE,
                source TEXT,
                published_date TEXT,
                sentiment_score REAL,
                sentiment_label TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                news_id INTEGER,
                alert_type TEXT,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (news_id) REFERENCES news (id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS monitor_status (
                id INTEGER PRIMARY KEY,
                last_check TIMESTAMP,
                status TEXT,
                message TEXT
            )
        ''')

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    def calculate_sentiment(self, text: str) -> Tuple[float, str]:
        """
        Calculate sentiment score for text
        Returns: (score, label) where score is -1 to 1, label is 'positive', 'negative', or 'neutral'
        """
        if not text:
            return 0.0, 'neutral'

        text_lower = text.lower()

        positive_count = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in text_lower)
        negative_count = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in text_lower)

        total_keywords = positive_count + negative_count
        if total_keywords == 0:
            return 0.0, 'neutral'

        score = (positive_count - negative_count) / total_keywords

        if score > 0.3:
            label = 'positive'
        elif score < -0.3:
            label = 'negative'
        else:
            label = 'neutral'

        return score, label

    def fetch_google_news(self, ticker: str) -> List[Dict]:
        """Fetch news from Google News RSS feed"""
        articles = []
        try:
            # Google News RSS feed for specific stock
            url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)

            for entry in feed.entries[:10]:  # Get latest 10 articles
                article = {
                    'ticker': ticker,
                    'title': entry.get('title', ''),
                    'description': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'source': 'Google News',
                    'published_date': entry.get('published', datetime.now().isoformat())
                }
                articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching Google News for {ticker}: {e}")

        return articles

    def fetch_yahoo_finance_rss(self, ticker: str) -> List[Dict]:
        """Fetch news from Yahoo Finance RSS feed"""
        articles = []
        try:
            url = f"https://finance.yahoo.com/rss/headline?s={ticker}"
            feed = feedparser.parse(url)

            for entry in feed.entries[:5]:
                article = {
                    'ticker': ticker,
                    'title': entry.get('title', ''),
                    'description': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'source': 'Yahoo Finance',
                    'published_date': entry.get('published', datetime.now().isoformat())
                }
                articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance for {ticker}: {e}")

        return articles

    def save_news(self, article: Dict) -> int:
        """Save news article to database and return news_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate sentiment
        full_text = f"{article['title']} {article.get('description', '')}"
        sentiment_score, sentiment_label = self.calculate_sentiment(full_text)

        try:
            cursor.execute('''
                INSERT INTO news (ticker, title, description, url, source, published_date, sentiment_score, sentiment_label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article['ticker'],
                article['title'],
                article.get('description', ''),
                article['url'],
                article['source'],
                article['published_date'],
                sentiment_score,
                sentiment_label
            ))

            news_id = cursor.lastrowid
            conn.commit()

            # Create alert if sentiment is positive
            if sentiment_label == 'positive' and sentiment_score > 0.3:
                self.create_alert(cursor, article['ticker'], news_id, 'POSITIVE_NEWS',
                                f"Positive news detected for {article['ticker']}: {article['title']}")
                conn.commit()

            conn.close()
            return news_id

        except sqlite3.IntegrityError:
            # Article already exists
            conn.close()
            return -1
        except Exception as e:
            logger.error(f"Error saving news: {e}")
            conn.close()
            return -1

    def create_alert(self, cursor, ticker: str, news_id: int, alert_type: str, message: str):
        """Create an alert"""
        cursor.execute('''
            INSERT INTO alerts (ticker, news_id, alert_type, message)
            VALUES (?, ?, ?, ?)
        ''', (ticker, news_id, alert_type, message))
        logger.info(f"🔔 ALERT: {message}")

    def update_monitor_status(self, status: str, message: str):
        """Update monitor status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO monitor_status (id, last_check, status, message)
            VALUES (1, ?, ?, ?)
        ''', (datetime.now().isoformat(), status, message))

        conn.commit()
        conn.close()

    def check_news_for_all_stocks(self):
        """Check news for all monitored stocks"""
        logger.info(f"Checking news for {len(STOCKS)} stocks...")
        total_new_articles = 0

        for ticker in STOCKS:
            logger.info(f"Fetching news for {ticker}...")

            # Fetch from multiple sources
            articles = []
            articles.extend(self.fetch_google_news(ticker))
            articles.extend(self.fetch_yahoo_finance_rss(ticker))

            # Save articles
            new_count = 0
            for article in articles:
                news_id = self.save_news(article)
                if news_id > 0:
                    new_count += 1

            if new_count > 0:
                logger.info(f"  Found {new_count} new articles for {ticker}")
                total_new_articles += new_count

            # Small delay between requests
            time.sleep(1)

        status_msg = f"Checked {len(STOCKS)} stocks, found {total_new_articles} new articles"
        self.update_monitor_status('running', status_msg)
        logger.info(status_msg)

    def run(self):
        """Main monitoring loop - runs 24x7"""
        logger.info("🚀 Stock News Monitor started!")
        logger.info(f"Monitoring stocks: {', '.join(STOCKS)}")
        logger.info(f"Check interval: {CHECK_INTERVAL} seconds")

        while True:
            try:
                self.check_news_for_all_stocks()
                logger.info(f"Next check in {CHECK_INTERVAL} seconds...")
                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                self.update_monitor_status('stopped', 'Stopped by user')
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                self.update_monitor_status('error', str(e))
                time.sleep(60)  # Wait a minute before retrying


if __name__ == '__main__':
    monitor = StockNewsMonitor()
    monitor.run()
