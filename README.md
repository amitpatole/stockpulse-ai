# 📊 StockPulse AI

**24/7 Stock Market Intelligence with AI-Powered Analysis**

StockPulse AI is a comprehensive stock market monitoring system that tracks news, social media, and market sentiment from 10+ sources in real-time. It features AI-powered technical analysis combining RSI, moving averages, and sentiment scoring to provide actionable BUY/SELL/HOLD ratings.

![StockPulse AI Dashboard](https://via.placeholder.com/1200x600/667eea/ffffff?text=StockPulse+AI+Dashboard)

## ✨ Features

### 🔄 Real-Time Monitoring
- **24/7 automated monitoring** of stock news and social media
- **9+ data sources** including Google News, Yahoo Finance, Seeking Alpha, MarketWatch, Benzinga, Finviz, Reddit, StockTwits, and Twitter/X
- **Auto-refresh dashboard** updates every 10 seconds
- **Instant alerts** for positive news with sentiment scoring

### 🤖 AI-Powered Analysis
- **Technical indicators**: RSI, EMA, MACD, Moving Averages (MA-20, MA-50, MA-200)
- **Sentiment analysis**: 45+ positive and 50+ negative keywords with engagement weighting
- **AI ratings**: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL with confidence scores
- **Combined scoring**: 60% sentiment + 40% technical analysis

### 📈 Interactive Dashboard
- **Tabbed interface** for organized navigation
- **Stock cards** with sentiment indicators and click-to-filter
- **Dynamic stock management** - add/remove stocks with ticker search
- **Detailed AI analysis** with technical signals and sentiment breakdown
- **News & alerts feed** with sentiment labels and source tracking

### 🎯 Smart Features
- **Dynamic stock lists** - no code changes needed to add/remove stocks
- **Engagement scoring** - prioritizes high-engagement social media posts
- **Sentiment filtering** - positive/negative/neutral classification
- **Historical tracking** - SQLite database for trend analysis

## 🚀 Quick Start

### Prerequisites
- Python 3.12+ (required for SQLite support)
- Linux/macOS/WSL (recommended for 24/7 operation)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/stockpulse-ai.git
cd stockpulse-ai
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Initialize the database**
```bash
python3.12 stock_manager.py
```
This creates the database with 10 default stocks (GTI, APLD, INTC, USAR, CRML, NVTS, OKLO, HUT, IBIT, CGC).

4. **Start the system**
```bash
chmod +x run.sh
./run.sh
```

5. **Access the dashboard**
```
http://localhost:5000
```

## 📖 Usage Guide

### Managing Stocks

**Add a stock:**
1. Go to "Manage Stocks" tab
2. Type company name or ticker (e.g., "tesla", "TSLA")
3. Click "Add" on the desired result
4. Monitor starts automatically

**Remove a stock:**
1. Go to "Manage Stocks" tab
2. Click "Remove" next to the stock
3. Confirm removal

### Viewing AI Analysis

**Option 1: Auto-load from Overview**
1. Click a stock card in Overview tab
2. Switch to AI Analysis tab
3. Analysis loads automatically for selected stock

**Option 2: Manual selection**
1. Go to AI Analysis tab
2. Select stock from dropdown
3. Click "Analyze"

### Understanding AI Ratings

| Rating | Score Range | Meaning |
|--------|-------------|---------|
| 🚀 STRONG_BUY | 80-100 | Strong bullish signals across technical and sentiment |
| 📈 BUY | 65-79 | Positive signals, good entry opportunity |
| ➡️ HOLD | 50-64 | Mixed signals, maintain position |
| 📉 SELL | 35-49 | Negative signals, consider reducing position |
| 🔻 STRONG_SELL | 0-34 | Strong bearish signals, exit recommended |

**Technical Signals Include:**
- RSI oversold (<30) or overbought (>70)
- Price vs. moving averages (MA-20, MA-50, MA-200)
- EMA crossovers and MACD signals
- Momentum indicators

**Sentiment Signals Include:**
- News article sentiment trend
- Social media engagement scores
- Keyword frequency analysis
- High-impact news detection

## 🗂️ Project Structure

```
stockpulse-ai/
├── stock_monitor_enhanced.py   # Main 24/7 monitoring engine
├── dashboard.py                 # Flask web dashboard
├── ai_analytics.py             # AI-powered stock analysis
├── stock_manager.py            # Stock list management
├── templates/
│   └── dashboard.html          # Dashboard UI
├── requirements.txt            # Python dependencies
├── run.sh                      # Startup script
├── stock_news.db              # SQLite database (auto-created)
└── README.md                   # This file
```

## 📊 Data Sources

StockPulse AI aggregates data from these sources:

| Source | Type | Coverage | Update Frequency |
|--------|------|----------|------------------|
| Google News | News | Global | 5 minutes |
| Yahoo Finance | News + Data | Global | 5 minutes |
| Seeking Alpha | Analysis | Global | 5 minutes |
| MarketWatch | News | Global | 5 minutes |
| Benzinga | News | Global | 5 minutes |
| Finviz | News | US Markets | 5 minutes |
| Reddit | Social Media | 8 subreddits | 5 minutes |
| StockTwits | Social Media | Real-time | 5 minutes |
| Twitter/X | Social Media | Via Nitter | 5 minutes |

## 🔧 Configuration

### Monitoring Interval
Edit `stock_monitor_enhanced.py`:
```python
CHECK_INTERVAL = 300  # seconds (default: 5 minutes)
```

### Dashboard Port
Edit `dashboard.py`:
```python
app.run(host='0.0.0.0', port=5000)  # Change port here
```

### Sentiment Keywords
Add custom keywords in `stock_monitor_enhanced.py`:
```python
POSITIVE_KEYWORDS = ['your', 'keywords', ...]
NEGATIVE_KEYWORDS = ['your', 'keywords', ...]
```

### Reddit Configuration (Optional)
To enable full Reddit access, get API credentials from https://reddit.com/prefs/apps and update `stock_monitor_enhanced.py`:
```python
self.reddit = praw.Reddit(
    client_id='your_client_id',
    client_secret='your_client_secret',
    user_agent='StockPulse AI v1.0'
)
```

## 🛠️ Advanced Usage

### Running as Background Service

**Using systemd (recommended for production):**

1. Create service file `/etc/systemd/system/stockpulse-monitor.service`:
```ini
[Unit]
Description=StockPulse AI Monitor
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/stockpulse-ai
ExecStart=/usr/bin/python3.12 /path/to/stockpulse-ai/stock_monitor_enhanced.py
Restart=always

[Install]
WantedBy=multi-user.target
```

2. Create dashboard service `/etc/systemd/system/stockpulse-dashboard.service`:
```ini
[Unit]
Description=StockPulse AI Dashboard
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/stockpulse-ai
ExecStart=/usr/bin/python3.12 /path/to/stockpulse-ai/dashboard.py
Restart=always

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl enable stockpulse-monitor stockpulse-dashboard
sudo systemctl start stockpulse-monitor stockpulse-dashboard
```

### Database Management

**View database contents:**
```bash
sqlite3 stock_news.db "SELECT * FROM news ORDER BY created_at DESC LIMIT 10;"
```

**Export data:**
```bash
sqlite3 stock_news.db -header -csv "SELECT * FROM news;" > news_export.csv
```

**Clear old data:**
```bash
sqlite3 stock_news.db "DELETE FROM news WHERE created_at < datetime('now', '-30 days');"
```

## 📱 API Endpoints

StockPulse AI provides REST APIs for integration:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Monitor status and last check time |
| `/api/stocks` | GET | List all monitored stocks |
| `/api/stocks` | POST | Add new stock |
| `/api/stocks/<ticker>` | DELETE | Remove stock |
| `/api/news` | GET | Recent news articles |
| `/api/alerts` | GET | Recent alerts (positive news) |
| `/api/stats` | GET | Statistics for all stocks |
| `/api/ai/ratings` | GET | AI ratings for all stocks |
| `/api/ai/rating/<ticker>` | GET | AI rating for specific stock |

**Example API Usage:**
```bash
# Get AI rating for a stock
curl http://localhost:5000/api/ai/rating/TSLA

# Add a new stock
curl -X POST http://localhost:5000/api/stocks \
  -H "Content-Type: application/json" \
  -d '{"ticker": "TSLA", "name": "Tesla Inc"}'
```

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Setup
```bash
# Clone your fork
git clone https://github.com/yourusername/stockpulse-ai.git
cd stockpulse-ai

# Install dev dependencies
pip install -r requirements.txt

# Run tests (if available)
python -m pytest
```

## 📝 License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)** - see the [LICENSE](LICENSE) file for details.

**What this means:**
- ✓ You can use, modify, and distribute this software
- ✓ Commercial use is allowed (with restrictions below)
- ✗ You CANNOT sell closed-source versions
- ✗ You CANNOT remove attribution to the original author
- ✗ Any modifications MUST be shared under GPL-3.0

**Attribution Required:** All use must credit Amit Patole and link to https://github.com/amitpatole/stockpulse-ai

## ⚠️ Disclaimer

**IMPORTANT:** StockPulse AI is for informational and educational purposes only. It is NOT financial advice.

- Do not make investment decisions based solely on this tool
- Always do your own research (DYOR)
- Consult with a licensed financial advisor before making investment decisions
- Past performance does not guarantee future results
- The creators are not responsible for any financial losses

## 🙏 Acknowledgments

- Data sources: Google News, Yahoo Finance, Seeking Alpha, MarketWatch, Benzinga, Finviz, Reddit, StockTwits
- Technical analysis inspired by traditional trading indicators
- Built with Flask, BeautifulSoup, yfinance, and other amazing open-source libraries

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/stockpulse-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/stockpulse-ai/discussions)

---

**Made with ❤️ for retail investors and traders**

*Star ⭐ this repository if you found it helpful!*
