# 📊 StockPulse AI

**Version 2.0.0** - Real AI Integration Update

**24/7 Stock Market Intelligence with AI-Powered Analysis**

StockPulse AI is a comprehensive stock market monitoring system that tracks news, social media, and market sentiment from 10+ sources in real-time. It features AI-powered technical analysis combining RSI, moving averages, and sentiment scoring to provide actionable BUY/SELL/HOLD ratings.

![StockPulse AI Dashboard](https://via.placeholder.com/1200x600/667eea/ffffff?text=StockPulse+AI+Dashboard)

## ✨ Features

### 🌍 Multi-Market Support
- **US & India markets** - Track stocks from both markets simultaneously
- **Market-specific sources** - India stocks (.NS/.BO) get additional coverage from Economic Times, Moneycontrol, and Mint
- **Market filtering** - Filter dashboard by US, India, or view all markets together
- **NSE & BSE support** - Full coverage of National Stock Exchange and Bombay Stock Exchange

### 🔄 Real-Time Monitoring
- **24/7 automated monitoring** of stock news and social media
- **12+ data sources** including:
  - **Global**: Google News, Yahoo Finance, Seeking Alpha, MarketWatch, Benzinga, Finviz, Reddit, StockTwits, Twitter/X
  - **India**: Economic Times, Moneycontrol, Mint (for .NS/.BO stocks)
- **Auto-refresh dashboard** updates every 10 seconds
- **Instant alerts** for positive news with sentiment scoring

### 🤖 AI-Powered Analysis
- **Real AI Integration**: Connect OpenAI (ChatGPT), Anthropic (Claude), Google (Gemini), or xAI (Grok)
- **Technical indicators**: RSI, EMA, MACD, Moving Averages (MA-20, MA-50, MA-200)
- **Sentiment analysis**: 45+ positive and 50+ negative keywords with engagement weighting
- **AI ratings**: STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL with confidence scores
- **Combined scoring**: 60% sentiment + 40% technical analysis
- **Natural language insights**: When AI is configured, get human-readable analysis and recommendations

### 📈 Interactive Dashboard
- **Tabbed interface** for organized navigation (Overview, AI Analysis, Manage Stocks, Settings)
- **Stock cards** with sentiment indicators and click-to-filter
- **Interactive price charts** - view historical stock prices with multiple time periods (1D to 5Y)
- **Dynamic stock management** - add/remove stocks with ticker search
- **Detailed AI analysis** with technical signals and sentiment breakdown
- **News & alerts feed** with sentiment labels and source tracking
- **AI Provider settings** - easily configure and test AI integrations

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
This creates the database with 20 default stocks:
- **US**: TSLA, AAPL, MSFT, NVDA, GOOGL, AMZN, META, NFLX, AMD, COIN
- **India (NSE)**: RELIANCE.NS, TCS.NS, HDFCBANK.NS, INFY.NS, ICICIBANK.NS
- **India (BSE)**: RELIANCE.BO, TCS.BO, HDFCBANK.BO, INFY.BO, ICICIBANK.BO

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

### Market Filtering

**Filter stocks by market:**
1. Use the market dropdown at the top of the dashboard
2. Select "US", "India (NSE/BSE)", or "All Markets"
3. Dashboard, stats, and AI analysis update automatically
4. Filter persists across tabs

### Managing Stocks

**Add a stock:**
1. Go to "Manage Stocks" tab
2. Type company name or ticker (e.g., "tesla", "TSLA", "RELIANCE.NS")
3. Click "Add" on the desired result
4. Monitor starts automatically
5. Market is auto-detected from ticker suffix (.NS/.BO = India)

**Remove a stock:**
1. Go to "Manage Stocks" tab
2. Click "Remove" next to the stock
3. Confirm removal

**Adding Indian stocks:**
- NSE stocks: Add `.NS` suffix (e.g., "RELIANCE.NS", "TCS.NS")
- BSE stocks: Add `.BO` suffix (e.g., "RELIANCE.BO", "TCS.BO")
- Yahoo Finance ticker search will show both exchanges

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

### Global Sources (All Stocks)
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

### India-Specific Sources (NSE/BSE Stocks Only)
| Source | Type | Coverage | Update Frequency |
|--------|------|----------|------------------|
| Economic Times | News | India | 5 minutes |
| Moneycontrol | News + Analysis | India | 5 minutes |
| Mint (Livemint) | News | India | 5 minutes |

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

### AI Provider Configuration

⚠️ **SECURITY WARNING - READ CAREFULLY** ⚠️

StockPulse AI supports real AI integration with OpenAI (ChatGPT), Anthropic (Claude), Google (Gemini), and xAI (Grok) for enhanced stock analysis.

**IMPORTANT SECURITY NOTICE:**
- **API keys are stored in PLAIN TEXT in the local SQLite database**
- This application is designed for **SELF-HOSTED, PERSONAL USE ONLY**
- **DO NOT expose this dashboard to the public internet**
- **DO NOT share your database file** (`stock_news.db`)
- **YOU are responsible for the security of your API keys**
- Use only on localhost or secure private networks
- Consider using API key restrictions/limits on the provider's side

**Setting up AI Providers:**

1. **Go to Settings Tab** in the dashboard (⚙️ Settings)

2. **Get your API key** from one of these providers:
   - **OpenAI**: https://platform.openai.com/api-keys
   - **Anthropic**: https://console.anthropic.com/settings/keys
   - **Google**: https://makersuite.google.com/app/apikey
   - **xAI (Grok)**: https://console.x.ai

3. **Configure in Dashboard:**
   - Select your AI provider
   - Choose the model (e.g., gpt-4, claude-3-5-sonnet, gemini-pro)
   - Enter your API key
   - Click "Test Connection" to verify
   - Click "Save & Activate" to enable

4. **AI Features** (when configured):
   - Enhanced sentiment analysis with real AI
   - Natural language stock analysis and recommendations
   - Intelligent news summarization
   - Context-aware market insights

**Supported Models:**
- **OpenAI**: GPT-4o (recommended), GPT-4o Mini, GPT-4 Turbo, GPT-4, GPT-3.5 Turbo
- **Anthropic**: Claude 3.5 Sonnet (recommended), Claude 3.5 Haiku, Claude 3 Opus, Claude 3 Sonnet, Claude 3 Haiku
- **Google**: Gemini 2.5 Flash (recommended), Gemini 2.5 Pro, Gemini 2.0 Flash, Gemini Flash Latest, Gemini Pro Latest
- **xAI**: Grok Beta, Grok-2-1212

**Cost Considerations:**
- AI providers charge per API call
- Monitor your usage on the provider's dashboard
- Set up billing alerts to avoid unexpected charges
- The system works without AI configuration (uses technical analysis only)

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
| `/api/chart/<ticker>` | GET | Historical price data for charts |
| `/api/settings/ai-providers` | GET | List configured AI providers |
| `/api/settings/ai-provider` | POST | Add/update AI provider |
| `/api/settings/test-ai` | POST | Test AI provider connection |

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
