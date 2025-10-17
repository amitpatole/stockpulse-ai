# Enhanced Stock News Monitor

A comprehensive 24x7 stock news monitoring system that tracks news from **10+ FREE sources** including social media, financial news sites, and special monitoring for influential figures like Donald Trump.

## Monitored Stocks

- GTI
- APLD
- INTC
- USAR
- CRML
- NVTS
- OKLO
- HUT
- IBIT
- CGC

## Data Sources (10+)

### Financial News Sites
1. **Google News** - Aggregated news from thousands of sources
2. **Yahoo Finance** - Real-time market news and analysis
3. **Seeking Alpha** - Investment research and analysis
4. **MarketWatch** - Stock market and financial news
5. **Benzinga** - Breaking financial news
6. **Finviz** - Financial visualizations and news

### Social Media & Forums
7. **Reddit** - Monitors 8 major investing subreddits:
   - r/wallstreetbets
   - r/stocks
   - r/investing
   - r/pennystocks
   - r/StockMarket
   - r/options
   - r/thetagang
   - r/Daytrading

8. **StockTwits** - Real-time stock market social network

9. **Twitter/X** - Via Nitter proxy for tweets about stocks

### Special Sources
10. **Trump Posts & Policy News**:
    - Truth Social posts (when mentioning stocks)
    - Google News for Trump + stock mentions
    - Trump tariff and trade policy news
    - Trump economic statements

> Trump's statements can significantly impact markets, so this source is given high priority with engagement score boosting.

## Enhanced Features

### Advanced Sentiment Analysis
- **Keyword-based scoring** with 45+ positive and 50+ negative keywords
- **Engagement weighting** - Popular posts get sentiment score boost
- **Trump-specific prioritization** - High engagement scores for Trump-related news
- **Real-time scoring** from -1 (very negative) to +1 (very positive)

### Smart Alerts
- Only alerts on **positive sentiment** (score > 0.3)
- Filters out noise and negative news automatically
- Desktop browser notifications
- Real-time dashboard updates

### Data Quality
- **Duplicate detection** - URLs are unique to prevent duplicate alerts
- **Source attribution** - Every article shows its source
- **Engagement metrics** - Reddit upvotes, comments, StockTwits likes tracked
- **Database indexing** - Fast queries even with thousands of articles

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make scripts executable:
```bash
chmod +x run.sh stop.sh
```

## Usage

### Start the Monitor

```bash
./run.sh
```

This starts both the enhanced news monitoring service and web dashboard.

### Access the Dashboard

Open your browser and navigate to:
```
http://localhost:5000
```

### View Logs

Monitor logs in real-time:
```bash
tail -f monitor.log dashboard.log
```

View monitor logs only:
```bash
tail -f monitor.log
```

### Stop the Monitor

```bash
./stop.sh
```

## Dashboard Features

### Status Bar
- Real-time monitoring status
- Last check timestamp
- Summary of current activity

### Statistics Panel
- Total alerts in last 24 hours
- Number of monitored stocks (10)
- List of all data sources being monitored

### Stock Cards
- Individual sentiment overview for each stock
- Color-coded indicators (Green=Positive, Red=Negative, Gray=Neutral)
- Article count for each stock

### Recent Alerts Panel
- Shows **only positive news** (buying opportunities)
- Sentiment score percentage
- Source attribution
- Direct links to original articles
- Auto-updates every 10 seconds
- Browser notifications for new alerts

### Latest News Feed
- Shows all recent articles from all sources
- Color-coded by sentiment
- Ticker symbols clearly displayed
- Source names shown
- Clickable links to full articles

## How It Works

### News Collection Process

Every 5 minutes, the monitor:
1. Fetches news for each of the 10 stocks
2. Queries all 10+ data sources
3. Processes and deduplicates articles
4. Analyzes sentiment
5. Creates alerts for positive news
6. Updates the dashboard database

### Sentiment Calculation

```
Base Score = (positive_keywords - negative_keywords) / total_keywords

If engagement > 100: score *= 1.1
If engagement > 500: score *= 1.2

Final Score is clamped to [-1, 1]

Positive: score > 0.3
Negative: score < -0.3
Neutral: -0.3 <= score <= 0.3
```

### Alert Criteria

An alert is created when:
- Sentiment label is 'positive'
- Sentiment score > 0.3
- Article is not a duplicate

### Trump Monitoring

Trump monitoring uses 3 methods:
1. **Direct news search** - "Trump + [ticker]" on Google News
2. **Truth Social scraping** - Attempts to fetch from @realDonaldTrump
3. **Policy news** - Trump + tariff/trade/policy + ticker

Articles prefixed with `[TRUMP]`, `[TRUMP TRUTH SOCIAL]`, or `[TRUMP POLICY]` for easy identification.

## Configuration

### Change Check Interval

Edit `stock_monitor_enhanced.py`:
```python
CHECK_INTERVAL = 300  # seconds (default: 5 minutes)
```

### Modify Monitored Stocks

Edit `stock_monitor_enhanced.py`:
```python
STOCKS = ['GTI', 'APLD', 'INTC', ...]
```

### Adjust Reddit Subreddits

Edit `stock_monitor_enhanced.py`:
```python
REDDIT_SUBREDDITS = ['wallstreetbets', 'stocks', ...]
```

### Fine-tune Sentiment Keywords

Edit the keyword lists in `stock_monitor_enhanced.py`:
```python
POSITIVE_KEYWORDS = [...]
NEGATIVE_KEYWORDS = [...]
```

### Change Dashboard Port

Edit `dashboard.py`:
```python
app.run(host='0.0.0.0', port=5000, debug=False)
```

## Database Schema

SQLite database: `stock_news.db`

### Tables

**news**
- id, ticker, title, description, url (unique)
- source, published_date
- sentiment_score, sentiment_label
- engagement_score
- created_at

**alerts**
- id, ticker, news_id (foreign key)
- alert_type, message
- created_at

**monitor_status**
- id (always 1), last_check, status, message

### Indexes
- idx_ticker - Fast ticker lookups
- idx_created_at - Fast date range queries
- idx_sentiment - Fast sentiment filtering

## Advanced Usage

### Query Database Directly

```bash
# View all positive alerts
sqlite3 stock_news.db "SELECT ticker, title, sentiment_score FROM news WHERE sentiment_label='positive' ORDER BY created_at DESC LIMIT 10;"

# Count articles by source
sqlite3 stock_news.db "SELECT source, COUNT(*) as count FROM news GROUP BY source ORDER BY count DESC;"

# View Trump-related news
sqlite3 stock_news.db "SELECT ticker, title, source FROM news WHERE source LIKE '%Trump%' ORDER BY created_at DESC;"

# Articles with high engagement
sqlite3 stock_news.db "SELECT ticker, title, engagement_score FROM news WHERE engagement_score > 100 ORDER BY engagement_score DESC LIMIT 10;"
```

### Reddit Configuration (Optional)

For better Reddit access, get API credentials:
1. Go to https://www.reddit.com/prefs/apps
2. Create an app (script type)
3. Update `stock_monitor_enhanced.py`:
```python
self.reddit = praw.Reddit(
    client_id='YOUR_CLIENT_ID',
    client_secret='YOUR_CLIENT_SECRET',
    user_agent=USER_AGENT,
)
```

Without credentials, Reddit monitoring may be limited but will still work in read-only mode.

### Running as System Service

Create `/etc/systemd/system/stock-monitor.service`:
```ini
[Unit]
Description=Enhanced Stock News Monitor
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/ubuntu/marketwatch
ExecStart=/usr/bin/python3 stock_monitor_enhanced.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/stock-dashboard.service`:
```ini
[Unit]
Description=Stock Monitor Dashboard
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/home/ubuntu/marketwatch
ExecStart=/usr/bin/python3 dashboard.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable stock-monitor stock-dashboard
sudo systemctl start stock-monitor stock-dashboard
```

## Troubleshooting

### No news appearing
- Check internet connection
- Verify monitor.log for errors
- Some sources may be rate-limited (this is normal)
- Reddit requires PRAW library

### Dashboard not loading
- Ensure port 5000 is not in use: `lsof -i :5000`
- Check dashboard.log for errors
- Verify Flask is installed: `pip show flask`

### No alerts showing
- Alerts only appear for positive news
- Wait 5 minutes for first check cycle
- Check if any stocks have positive news in monitor.log

### Reddit not working
- Reddit can work without API keys in limited mode
- For full access, configure PRAW credentials
- Check if subreddits are accessible

### Twitter/Nitter not working
- Nitter instances can be unreliable
- The monitor tries 3 different instances
- Twitter monitoring is bonus; other sources will still work

### Trump monitoring not getting results
- Truth Social may block scraping attempts
- Google News searches for Trump mentions still work
- This is a best-effort feature

## Performance

- **Check interval**: 5 minutes per cycle
- **Sources per stock**: 10+ sources
- **Total queries**: 100+ per cycle (10 stocks × 10 sources)
- **Database size**: ~1MB per 1000 articles
- **Memory usage**: ~100-200MB
- **CPU usage**: Low, spikes during check cycles

## Privacy & Rate Limiting

- All scraping respects robots.txt
- User-Agent identifies as standard browser
- Delays between requests prevent rate limiting
- No authentication required for most sources
- Read-only access to all sources

## Legal & Ethical Use

This tool is for:
- Personal investment research
- Educational purposes
- Monitoring public information

This tool should NOT be used for:
- High-frequency trading
- Manipulating markets
- Violating terms of service
- Commercial redistribution

## Future Enhancements

Potential additions:
- Technical analysis integration
- Price tracking alongside news
- Email/SMS notifications
- Custom webhook support
- Machine learning sentiment analysis
- More social media sources
- International news sources
- Crypto news monitoring

## Credits

Built with:
- Python 3
- Flask (web dashboard)
- BeautifulSoup4 (web scraping)
- PRAW (Reddit API)
- Feedparser (RSS feeds)
- SQLite (database)

## License

MIT License - Free to use and modify for personal use
