# TickerPulse AI

**Version 3.0** - Multi-Agent Research Desk

24/7 stock market intelligence with AI-powered multi-agent analysis, automated research briefs, and real-time monitoring across 12+ data sources.

TickerPulse AI is a **research and monitoring tool** - it does not execute trades or provide financial advice. All trading decisions are made by humans.

---

## What's New in v3.0

- **Multi-Agent System**: 4 specialized AI agents (Scanner, Researcher, Regime, Investigator) working autonomously
- **Dual Agent Frameworks**: Choose between CrewAI (Python-native) or OpenClaw (WebSocket bridge)
- **Automated Scheduling**: 18+ configurable jobs (morning briefing, technical monitor, Reddit scanner, daily summary, etc.)
- **React Dashboard**: Modern Next.js frontend with real-time SSE updates, TradingView charts, agent mission control
- **Pluggable Data Providers**: Bring your own data subscriptions (Polygon, Finnhub, Alpha Vantage, and more) with automatic fallback chain
- **Cost Tracking**: Per-agent token usage and cost monitoring with configurable budget limits

## Architecture

```
  React/Next.js Frontend (port 3000)
          |
          | REST + SSE
          v
  Flask Backend (port 5000)
    ├── Agent Layer (CrewAI / OpenClaw)
    │     ├── Scanner    (Haiku 4.5)   - Stock scanning & ranking
    │     ├── Researcher (Sonnet 4.5)  - Deep research briefs
    │     ├── Regime     (Sonnet 4.5)  - Market regime classification
    │     └── Investigator (Haiku 4.5) - Social media monitoring
    ├── Scheduler (APScheduler, 18+ jobs)
    ├── Data Providers (pluggable, fallback chain)
    └── SQLite Database
```

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm

### One-Command Install

**Linux / macOS:**
```bash
git clone https://github.com/amitpatole/tickerpulse-ai.git
cd tickerpulse-ai
bash install.sh
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/amitpatole/tickerpulse-ai.git
cd tickerpulse-ai
.\install.ps1
```

The installer checks prerequisites, creates a Python virtual environment, installs all dependencies, builds the frontend, and sets up your `.env` file.

After installation:
1. Edit `.env` and add at least one AI provider API key (Anthropic, OpenAI, Google, or xAI)
2. Run `./run.sh` to start
3. Open http://localhost:3000

### Manual Installation

<details>
<summary>Click to expand manual steps</summary>

```bash
git clone https://github.com/amitpatole/tickerpulse-ai.git
cd tickerpulse-ai

# Environment config
cp .env.example .env
# Edit .env with your API keys (at minimum, set ANTHROPIC_API_KEY)

# Python virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install
npm run build
cd ..

# Start
chmod +x run.sh stop.sh
./run.sh
```

</details>

**Dashboard**: http://localhost:3000
**API**: http://localhost:5000
**Legacy Dashboard**: http://localhost:5000/legacy

### Docker (Alternative)

```bash
cp .env.example .env
# Edit .env with your API keys
docker compose up -d
```

## Features

### Multi-Agent System

| Agent | Model | Role | Schedule |
|-------|-------|------|----------|
| Scanner | Haiku 4.5 | Scan stocks, compute technicals, rank opportunities | Every 15 min (market hours) |
| Researcher | Sonnet 4.5 | Generate comprehensive research briefs | On-demand |
| Regime | Sonnet 4.5 | Market regime classification (risk-on/off) | Every 2 hours |
| Investigator | Haiku 4.5 | Reddit/social media monitoring | Hourly |

Agents can be triggered manually via the dashboard or run on automated schedules.

### Data Sources

**News & Social** (12+ sources):
Google News, Yahoo Finance, Seeking Alpha, MarketWatch, Benzinga, Finviz, Reddit (8 subreddits), StockTwits, Twitter/X

**India-Specific** (for .NS/.BO stocks):
Economic Times, Moneycontrol, Mint

### Pluggable Data Providers

Bring your own premium data subscriptions:

| Provider | Cost | Real-Time | Setup |
|----------|------|-----------|-------|
| Yahoo Finance (yfinance) | Free | 15-min delay | Built-in, no key needed |
| Polygon.io | $29-199/mo | Yes (paid) | Set `POLYGON_API_KEY` |
| Alpha Vantage | Free-$49/mo | Varies | Set `ALPHA_VANTAGE_KEY` |
| Finnhub | Free-$49/mo | 15-min (free) | Set `FINNHUB_API_KEY` |
| Custom | N/A | Varies | Implement `DataProvider` ABC |

Providers are tried in priority order with automatic fallback. yfinance is always the last resort.

### Technical Indicators

RSI, MACD, EMA, Moving Averages (MA-20, MA-50, MA-200), Bollinger Bands, ATR, VWAP, OBV, Stochastic Oscillator

### AI Providers

Configure via the Settings page or `.env`:

| Provider | Models |
|----------|--------|
| Anthropic (Claude) | Haiku 4.5, Sonnet 4.5, Opus 4.6 |
| OpenAI | GPT-4o, GPT-4.1 |
| Google | Gemini 2.5 Flash, Gemini 2.5 Pro |
| xAI | Grok-4, Grok-4-Vision |

### Multi-Market Support

- **US Markets**: NYSE, NASDAQ
- **India Markets**: NSE (.NS suffix), BSE (.BO suffix)
- Market-aware scheduling (jobs respect market hours)

## Project Structure

```
tickerpulse-ai/
├── backend/
│   ├── app.py              # Flask app factory
│   ├── config.py            # Central configuration
│   ├── database.py          # SQLite connection manager
│   ├── scheduler.py         # APScheduler setup
│   ├── api/                 # REST API routes (6 blueprints)
│   ├── core/                # Original TickerPulse modules
│   ├── agents/              # Multi-agent system
│   │   ├── base.py          # Agent registry & base classes
│   │   ├── crewai_engine.py # CrewAI orchestration
│   │   ├── openclaw_engine.py # OpenClaw bridge
│   │   ├── scanner_agent.py
│   │   ├── researcher_agent.py
│   │   ├── regime_agent.py
│   │   ├── investigator_agent.py
│   │   └── tools/           # CrewAI custom tools
│   ├── data_providers/      # Pluggable data provider system
│   └── jobs/                # Scheduled job definitions
├── frontend/                # React/Next.js dashboard
├── templates/               # Legacy HTML dashboard
├── docker-compose.yml
├── .env.example
└── CLAUDE.md                # Development guide
```

## API Endpoints

### Stocks
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stocks` | GET | List monitored stocks |
| `/api/stocks` | POST | Add stock |
| `/api/stocks/<ticker>` | DELETE | Remove stock |

### Analysis
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/ai/ratings` | GET | AI ratings for all stocks |
| `/api/ai/rating/<ticker>` | GET | AI rating for one stock |
| `/api/news` | GET | Recent news articles |
| `/api/alerts` | GET | Recent alerts |

### Agents
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/agents` | GET | List all agents with status |
| `/api/agents/<name>/run` | POST | Trigger agent manually |
| `/api/agents/runs` | GET | Agent run history |
| `/api/agents/costs` | GET | Cost summary |

### Scheduler
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scheduler/jobs` | GET | List scheduled jobs |
| `/api/scheduler/jobs/<id>/trigger` | POST | Trigger job now |
| `/api/scheduler/jobs/<id>/pause` | POST | Pause job |
| `/api/scheduler/jobs/<id>/resume` | POST | Resume job |

### Real-Time
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stream` | GET | SSE stream for live updates |
| `/api/health` | GET | Health check |

## Estimated API Costs

| Component | Daily | Monthly |
|-----------|-------|---------|
| Scanner (Haiku, 5x/day) | $8-15 | $175-330 |
| Technical Monitor (Haiku, 15-min) | $5-10 | $110-220 |
| Researcher (Sonnet, on-demand) | $2-5 | $44-110 |
| Regime (Sonnet, 4x/day) | $1-3 | $22-66 |
| Investigator (Haiku, hourly) | $1-3 | $22-66 |
| **Total** | **$17-36** | **$373-792** |

Budget limits are configurable via `MONTHLY_BUDGET_LIMIT` and `DAILY_BUDGET_WARNING`.

## Configuration

All settings can be configured via environment variables (`.env` file) or the Settings page in the dashboard. See `.env.example` for all available options.

## Inspiration & Acknowledgment

The multi-agent enhancement in TickerPulse AI v3.0 was inspired by a [Reddit post](https://www.reddit.com/r/openclaw/comments/1r1lp3n/) describing a multi-agent AI workflow built with OpenClaw. The concept of specialized AI agents collaborating on market research motivated our own independent implementation. This work is inspired by, not copied from, the original post -- all code, architecture, and design decisions are original to the TickerPulse AI project.

TickerPulse AI is a research and monitoring tool -- it does not execute trades or provide financial advice.

## Disclaimer

**IMPORTANT:** TickerPulse AI is for informational and educational purposes only. It is NOT financial advice.

- Do not make investment decisions based solely on this tool
- Always do your own research (DYOR)
- Consult with a licensed financial advisor before making investment decisions
- Past performance does not guarantee future results
- The creators are not responsible for any financial losses

## License

This project is licensed under the **GNU General Public License v3.0 (GPL-3.0)** - see the [LICENSE](LICENSE) file for details.

**Attribution Required:** All use must credit Amit Patole and link to https://github.com/amitpatole/tickerpulse-ai

## Acknowledgments

- Data sources: Google News, Yahoo Finance, Seeking Alpha, MarketWatch, Benzinga, Finviz, Reddit, StockTwits
- Technical analysis based on standard trading indicators
- Built with Flask, Next.js, CrewAI, TradingView Lightweight Charts, and other open-source libraries

---

**Made for retail investors and researchers**
