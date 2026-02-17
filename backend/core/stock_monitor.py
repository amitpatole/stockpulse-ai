#!/usr/bin/env python3
"""
TickerPulse AI - Enhanced Stock News Monitor
Tracks news from ALL available free sources with AI-powered analysis
24/7 market intelligence and sentiment tracking
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
from bs4 import BeautifulSoup
from urllib.parse import quote
import praw

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# News check interval (in seconds) - 5 minutes
CHECK_INTERVAL = 300

# User agent for web scraping
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Positive and negative keywords for sentiment analysis
POSITIVE_KEYWORDS = [
    'surge', 'soar', 'rally', 'gain', 'rise', 'jump', 'climb', 'boost', 'upgrade',
    'bullish', 'positive', 'growth', 'profit', 'revenue', 'beat', 'exceed', 'outperform',
    'strong', 'robust', 'expansion', 'breakthrough', 'partnership', 'deal', 'acquisition',
    'innovation', 'success', 'award', 'win', 'record', 'high', 'optimistic', 'momentum',
    'buy', 'overweight', 'increased guidance', 'raised guidance', 'dividend increase',
    'approved', 'approval', 'contract', 'billion', 'million deal', 'expanding', 'moon',
    'rocket', 'skyrocket', 'explode', 'breakout', 'all-time high', 'ath', 'bullrun'
]

NEGATIVE_KEYWORDS = [
    'plunge', 'crash', 'drop', 'fall', 'decline', 'loss', 'bearish', 'negative',
    'downgrade', 'sell', 'underperform', 'weak', 'concern', 'warning', 'miss',
    'below', 'disappointed', 'cut', 'reduced guidance', 'lowered guidance', 'lawsuit',
    'investigation', 'fraud', 'scandal', 'bankrupt', 'debt', 'trouble', 'dump',
    'bleeding', 'tank', 'crater', 'plummet', 'tumble'
]

# Reddit subreddits to monitor
REDDIT_SUBREDDITS = [
    'wallstreetbets', 'stocks', 'investing', 'pennystocks',
    'StockMarket', 'options', 'thetagang', 'Daytrading'
]


class EnhancedStockNewsMonitor:
    def __init__(self, db_path='stock_news.db'):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT})
        self.init_database()
        self.reddit = None
        self.init_reddit()

    def init_reddit(self):
        """Initialize Reddit client (read-only mode)"""
        try:
            self.reddit = praw.Reddit(
                client_id='your_client_id',  # Will use without authentication in read-only mode
                client_secret='your_client_secret',
                user_agent=USER_AGENT,
                check_for_async=False
            )
            logger.info("Reddit client initialized")
        except Exception as e:
            logger.warning(f"Reddit client initialization failed (will skip Reddit): {e}")
            self.reddit = None

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
                engagement_score INTEGER DEFAULT 0,
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

        # Add index for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_ticker ON news(ticker)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_created_at ON news(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sentiment ON news(sentiment_label)')

        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    def get_active_stocks(self) -> List[str]:
        """Get list of active stocks from database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT ticker FROM stocks WHERE active = 1 ORDER BY ticker')
            stocks = [row['ticker'] for row in cursor.fetchall()]
            conn.close()
            return stocks
        except sqlite3.OperationalError:
            # Table doesn't exist yet, return empty list
            conn.close()
            logger.warning("Stocks table not found, no stocks to monitor")
            return []

    def calculate_sentiment(self, text: str, engagement_score: int = 0) -> Tuple[float, str]:
        """
        Enhanced sentiment calculation with engagement weighting
        Returns: (score, label) where score is -1 to 1
        """
        if not text:
            return 0.0, 'neutral'

        text_lower = text.lower()

        positive_count = sum(1 for keyword in POSITIVE_KEYWORDS if keyword in text_lower)
        negative_count = sum(1 for keyword in NEGATIVE_KEYWORDS if keyword in text_lower)

        total_keywords = positive_count + negative_count
        if total_keywords == 0:
            return 0.0, 'neutral'

        # Base sentiment score
        score = (positive_count - negative_count) / total_keywords

        # Boost score if high engagement (for Reddit/Twitter)
        if engagement_score > 100:
            score = score * 1.1
        elif engagement_score > 500:
            score = score * 1.2

        # Clamp score to [-1, 1]
        score = max(-1.0, min(1.0, score))

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
            url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en-US&gl=US&ceid=US:en"
            feed = feedparser.parse(url)

            for entry in feed.entries[:10]:
                article = {
                    'ticker': ticker,
                    'title': entry.get('title', ''),
                    'description': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'source': 'Google News',
                    'published_date': entry.get('published', datetime.now().isoformat()),
                    'engagement_score': 0
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
                    'published_date': entry.get('published', datetime.now().isoformat()),
                    'engagement_score': 0
                }
                articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching Yahoo Finance for {ticker}: {e}")

        return articles

    def fetch_seeking_alpha(self, ticker: str) -> List[Dict]:
        """Fetch news from Seeking Alpha"""
        articles = []
        try:
            url = f"https://seekingalpha.com/api/v3/symbols/{ticker}/news"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                for item in data.get('data', [])[:5]:
                    attrs = item.get('attributes', {})
                    article = {
                        'ticker': ticker,
                        'title': attrs.get('title', ''),
                        'description': attrs.get('summary', ''),
                        'url': f"https://seekingalpha.com{attrs.get('uri', '')}",
                        'source': 'Seeking Alpha',
                        'published_date': attrs.get('publishOn', datetime.now().isoformat()),
                        'engagement_score': 0
                    }
                    articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching Seeking Alpha for {ticker}: {e}")

        return articles

    def fetch_marketwatch(self, ticker: str) -> List[Dict]:
        """Fetch news from MarketWatch"""
        articles = []
        try:
            url = f"https://www.marketwatch.com/investing/stock/{ticker.lower()}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                news_items = soup.find_all('div', class_='article__content', limit=5)

                for item in news_items:
                    title_elem = item.find('a', class_='link')
                    if title_elem:
                        article = {
                            'ticker': ticker,
                            'title': title_elem.get_text(strip=True),
                            'description': '',
                            'url': title_elem.get('href', ''),
                            'source': 'MarketWatch',
                            'published_date': datetime.now().isoformat(),
                            'engagement_score': 0
                        }
                        if article['url'] and not article['url'].startswith('http'):
                            article['url'] = f"https://www.marketwatch.com{article['url']}"
                        articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching MarketWatch for {ticker}: {e}")

        return articles

    def fetch_benzinga(self, ticker: str) -> List[Dict]:
        """Fetch news from Benzinga RSS"""
        articles = []
        try:
            url = f"https://www.benzinga.com/feeds/atom/stock/{ticker}"
            feed = feedparser.parse(url)

            for entry in feed.entries[:5]:
                article = {
                    'ticker': ticker,
                    'title': entry.get('title', ''),
                    'description': entry.get('summary', ''),
                    'url': entry.get('link', ''),
                    'source': 'Benzinga',
                    'published_date': entry.get('published', datetime.now().isoformat()),
                    'engagement_score': 0
                }
                articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching Benzinga for {ticker}: {e}")

        return articles

    def fetch_reddit(self, ticker: str) -> List[Dict]:
        """Fetch posts from Reddit"""
        articles = []
        if not self.reddit:
            return articles

        try:
            for subreddit_name in REDDIT_SUBREDDITS:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)

                    # Search for ticker in the subreddit
                    for submission in subreddit.search(f"${ticker} OR {ticker}", limit=5, time_filter='day'):
                        article = {
                            'ticker': ticker,
                            'title': submission.title,
                            'description': submission.selftext[:500] if submission.selftext else '',
                            'url': f"https://reddit.com{submission.permalink}",
                            'source': f'Reddit r/{subreddit_name}',
                            'published_date': datetime.fromtimestamp(submission.created_utc).isoformat(),
                            'engagement_score': submission.score + submission.num_comments
                        }
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error fetching from r/{subreddit_name} for {ticker}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching Reddit for {ticker}: {e}")

        return articles

    def fetch_stocktwits(self, ticker: str) -> List[Dict]:
        """Fetch messages from StockTwits"""
        articles = []
        try:
            url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                for message in data.get('messages', [])[:10]:
                    sentiment = message.get('entities', {}).get('sentiment', {})
                    article = {
                        'ticker': ticker,
                        'title': message.get('body', '')[:200],
                        'description': message.get('body', ''),
                        'url': f"https://stocktwits.com/{message.get('user', {}).get('username', 'user')}/message/{message.get('id', '')}",
                        'source': 'StockTwits',
                        'published_date': message.get('created_at', datetime.now().isoformat()),
                        'engagement_score': message.get('likes', {}).get('total', 0)
                    }
                    articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching StockTwits for {ticker}: {e}")

        return articles

    def fetch_finviz_news(self, ticker: str) -> List[Dict]:
        """Fetch news from Finviz"""
        articles = []
        try:
            url = f"https://finviz.com/quote.ashx?t={ticker}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                news_table = soup.find('table', {'id': 'news-table'})

                if news_table:
                    rows = news_table.find_all('tr', limit=10)
                    for row in rows:
                        link = row.find('a')
                        if link:
                            article = {
                                'ticker': ticker,
                                'title': link.get_text(strip=True),
                                'description': '',
                                'url': link.get('href', ''),
                                'source': 'Finviz',
                                'published_date': datetime.now().isoformat(),
                                'engagement_score': 0
                            }
                            articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching Finviz for {ticker}: {e}")

        return articles

    def fetch_twitter_via_nitter(self, ticker: str) -> List[Dict]:
        """Fetch tweets via Nitter (Twitter alternative frontend)"""
        articles = []
        try:
            # Using public Nitter instance
            nitter_instances = ['nitter.net', 'nitter.poast.org', 'nitter.privacydev.net']

            for instance in nitter_instances:
                try:
                    url = f"https://{instance}/search?f=tweets&q=%24{ticker}+OR+{ticker}&since=&until=&near="
                    response = self.session.get(url, timeout=10)

                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        tweets = soup.find_all('div', class_='timeline-item', limit=5)

                        for tweet in tweets:
                            content = tweet.find('div', class_='tweet-content')
                            link = tweet.find('a', class_='tweet-link')

                            if content and link:
                                article = {
                                    'ticker': ticker,
                                    'title': content.get_text(strip=True)[:200],
                                    'description': content.get_text(strip=True),
                                    'url': f"https://twitter.com{link.get('href', '')}",
                                    'source': 'Twitter/X',
                                    'published_date': datetime.now().isoformat(),
                                    'engagement_score': 0
                                }
                                articles.append(article)

                        if articles:
                            break  # Successfully got tweets from this instance

                except Exception as e:
                    logger.debug(f"Nitter instance {instance} failed: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error fetching Twitter for {ticker}: {e}")

        return articles

    def fetch_economic_times(self, ticker: str) -> List[Dict]:
        """Fetch news from Economic Times (India) - only for .NS and .BO tickers"""
        articles = []
        if not ('.NS' in ticker.upper() or '.BO' in ticker.upper()):
            return articles

        try:
            # Remove .NS or .BO suffix for search
            clean_ticker = ticker.replace('.NS', '').replace('.BO', '').replace('.ns', '').replace('.bo', '')
            url = f"https://economictimes.indiatimes.com/topic/{clean_ticker}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                news_items = soup.find_all('div', class_='eachStory', limit=5)

                for item in news_items:
                    title_elem = item.find('h3')
                    link_elem = item.find('a')
                    if title_elem and link_elem:
                        article = {
                            'ticker': ticker,
                            'title': title_elem.get_text(strip=True),
                            'description': '',
                            'url': link_elem.get('href', ''),
                            'source': 'Economic Times (India)',
                            'published_date': datetime.now().isoformat(),
                            'engagement_score': 0
                        }
                        if article['url'] and not article['url'].startswith('http'):
                            article['url'] = f"https://economictimes.indiatimes.com{article['url']}"
                        articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching Economic Times for {ticker}: {e}")

        return articles

    def fetch_moneycontrol(self, ticker: str) -> List[Dict]:
        """Fetch news from Moneycontrol (India) - only for .NS and .BO tickers"""
        articles = []
        if not ('.NS' in ticker.upper() or '.BO' in ticker.upper()):
            return articles

        try:
            # Remove .NS or .BO suffix for search
            clean_ticker = ticker.replace('.NS', '').replace('.BO', '').replace('.ns', '').replace('.bo', '')
            url = f"https://www.moneycontrol.com/stocks/company_info/stock_news.php?sc_id={clean_ticker}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                news_items = soup.find_all('li', class_='clearfix', limit=5)

                for item in news_items:
                    link = item.find('a')
                    if link:
                        article = {
                            'ticker': ticker,
                            'title': link.get_text(strip=True),
                            'description': '',
                            'url': link.get('href', ''),
                            'source': 'Moneycontrol (India)',
                            'published_date': datetime.now().isoformat(),
                            'engagement_score': 0
                        }
                        if article['url'] and not article['url'].startswith('http'):
                            article['url'] = f"https://www.moneycontrol.com{article['url']}"
                        articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching Moneycontrol for {ticker}: {e}")

        return articles

    def fetch_mint(self, ticker: str) -> List[Dict]:
        """Fetch news from Mint/Livemint (India) - only for .NS and .BO tickers"""
        articles = []
        if not ('.NS' in ticker.upper() or '.BO' in ticker.upper()):
            return articles

        try:
            # Remove .NS or .BO suffix for search
            clean_ticker = ticker.replace('.NS', '').replace('.BO', '').replace('.ns', '').replace('.bo', '')
            url = f"https://www.livemint.com/Search/Link/Keyword/{clean_ticker}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                news_items = soup.find_all('h2', limit=5)

                for item in news_items:
                    link = item.find('a')
                    if link:
                        article = {
                            'ticker': ticker,
                            'title': link.get_text(strip=True),
                            'description': '',
                            'url': link.get('href', ''),
                            'source': 'Mint (India)',
                            'published_date': datetime.now().isoformat(),
                            'engagement_score': 0
                        }
                        if article['url'] and not article['url'].startswith('http'):
                            article['url'] = f"https://www.livemint.com{article['url']}"
                        articles.append(article)

        except Exception as e:
            logger.error(f"Error fetching Mint for {ticker}: {e}")

        return articles


    def save_news(self, article: Dict) -> int:
        """Save news article to database and return news_id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Calculate sentiment
        full_text = f"{article['title']} {article.get('description', '')}"
        sentiment_score, sentiment_label = self.calculate_sentiment(
            full_text,
            article.get('engagement_score', 0)
        )

        try:
            cursor.execute('''
                INSERT INTO news (ticker, title, description, url, source, published_date,
                                 sentiment_score, sentiment_label, engagement_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                article['ticker'],
                article['title'],
                article.get('description', ''),
                article['url'],
                article['source'],
                article['published_date'],
                sentiment_score,
                sentiment_label,
                article.get('engagement_score', 0)
            ))

            news_id = cursor.lastrowid
            conn.commit()

            # Create alert if sentiment is positive
            if sentiment_label == 'positive' and sentiment_score > 0.3:
                self.create_alert(cursor, article['ticker'], news_id, 'POSITIVE_NEWS',
                                f"Positive news detected for {article['ticker']}: {article['title'][:100]}")
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
        """Check news for all monitored stocks from ALL sources"""
        # Get current active stocks from database
        STOCKS = self.get_active_stocks()

        if not STOCKS:
            logger.warning("No active stocks to monitor. Add stocks via the dashboard.")
            self.update_monitor_status('running', 'No stocks to monitor. Add stocks via dashboard.')
            return

        logger.info(f"Checking news for {len(STOCKS)} stocks from multiple sources...")
        total_new_articles = 0
        source_stats = {}

        for ticker in STOCKS:
            logger.info(f"\n{'='*60}")
            logger.info(f"Fetching news for {ticker}...")
            logger.info(f"{'='*60}")

            # Fetch from ALL sources (global sources for all stocks)
            all_fetchers = [
                ('Google News', self.fetch_google_news),
                ('Yahoo Finance', self.fetch_yahoo_finance_rss),
                ('Seeking Alpha', self.fetch_seeking_alpha),
                ('MarketWatch', self.fetch_marketwatch),
                ('Benzinga', self.fetch_benzinga),
                ('Finviz', self.fetch_finviz_news),
                ('Reddit', self.fetch_reddit),
                ('StockTwits', self.fetch_stocktwits),
                ('Twitter/X', self.fetch_twitter_via_nitter),
            ]

            # Add India-specific sources for Indian stocks (.NS and .BO)
            is_indian_stock = '.NS' in ticker.upper() or '.BO' in ticker.upper()
            if is_indian_stock:
                india_fetchers = [
                    ('Economic Times', self.fetch_economic_times),
                    ('Moneycontrol', self.fetch_moneycontrol),
                    ('Mint', self.fetch_mint),
                ]
                all_fetchers.extend(india_fetchers)
                logger.info(f"  📍 Indian stock detected - including India-specific sources")

            ticker_new_count = 0

            for source_name, fetcher in all_fetchers:
                try:
                    logger.info(f"  Fetching from {source_name}...")
                    articles = fetcher(ticker)

                    source_count = 0
                    for article in articles:
                        news_id = self.save_news(article)
                        if news_id > 0:
                            source_count += 1
                            ticker_new_count += 1

                    if source_count > 0:
                        logger.info(f"    ✓ Found {source_count} new articles from {source_name}")
                        source_stats[source_name] = source_stats.get(source_name, 0) + source_count

                    # Small delay between sources
                    time.sleep(0.5)

                except Exception as e:
                    logger.error(f"    ✗ Error with {source_name}: {e}")

            if ticker_new_count > 0:
                logger.info(f"  Total: {ticker_new_count} new articles for {ticker}")
                total_new_articles += ticker_new_count

            # Delay between tickers
            time.sleep(2)

        # Log summary
        logger.info(f"\n{'='*60}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"Total new articles: {total_new_articles}")
        logger.info(f"Source breakdown:")
        for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {source}: {count} articles")

        status_msg = f"Checked {len(STOCKS)} stocks from {len(all_fetchers)} sources, found {total_new_articles} new articles"
        self.update_monitor_status('running', status_msg)
        logger.info(f"\n{status_msg}\n")

    def run(self):
        """Main monitoring loop - runs 24x7"""
        logger.info("🚀 TickerPulse AI - Enhanced Stock News Monitor started!")
        logger.info(f"Check interval: {CHECK_INTERVAL} seconds")
        logger.info(f"Global Sources: Google News, Yahoo Finance, Seeking Alpha, MarketWatch,")
        logger.info(f"                Benzinga, Finviz, Reddit, StockTwits, Twitter/X")
        logger.info(f"India Sources: Economic Times, Moneycontrol, Mint (for .NS/.BO stocks)")
        logger.info(f"")
        logger.info(f"Stocks are loaded dynamically from the database.")
        logger.info(f"Use the dashboard to add/remove stocks to monitor.")

        while True:
            try:
                self.check_news_for_all_stocks()
                logger.info(f"\nNext check in {CHECK_INTERVAL} seconds...\n")
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
    monitor = EnhancedStockNewsMonitor()
    monitor.run()
