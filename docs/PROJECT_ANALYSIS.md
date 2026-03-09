# TickerPulse AI - Project Analysis

**Version**: 3.0
**Last Updated**: 2026-03-03
**Status**: Production Research & Monitoring Platform

---

## 1. Executive Summary

**TickerPulse AI** is a 24/7 AI-powered stock market research and monitoring platform designed for retail investors and analysts. It combines multi-agent AI analysis, automated scheduling, pluggable data providers, and real-time dashboarding into a single integrated system.

**NOT a trading system** - TickerPulse provides research intelligence and monitoring only. All trading decisions remain human-controlled.

**Key Value Proposition**:
- Automate research workflow with 4 specialized AI agents running 18+ scheduled jobs
- Monitor 12+ data sources simultaneously (news, social, technical indicators)
- Support 5 AI providers (Anthropic, OpenAI, Google, xAI) with automatic fallback
- Track costs per agent with configurable monthly/daily budget limits
- Real-time SSE updates + historical analysis in single dashboard

---

## 2. Architecture Overview

### 2.1 System Architecture

```
┌──────────────────────────────────────────────────────┐
│  React/Next.js Frontend (port 3000)                  │
│  - Dashboard: Real-time SSE + TradingView charts     │
│  - Settings: API keys, budgets, framework selection  │
│  - Mission Control: Manual agent triggers + history  │
└────────────────────┬─────────────────────────────────┘
                     │ REST API + SSE
                     v
┌──────────────────────────────────────────────────────┐
│  Flask Backend (port 5000)                           │
│  ├─ Agent Layer                                       │
│  │  ├─ CrewAI Engine (Python-native agents)          │
│  │  └─ OpenClaw Engine (WebSocket bridge)            │
│  │  Agents: Scanner, Researcher, Regime, Investigator│
│  │  Download Tracker (GitHub stats)                  │
│  │                                                   │
│  ├─ Scheduler (APScheduler)                          │
│  │  18+ configurable jobs (respects market hours)    │
│  │                                                   │
│  ├─ Data Providers (Pluggable Chain)                 │
│  │  Primary: Polygon, Alpha Vantage, Finnhub         │
│  │  Fallback: yfinance (always available, free)      │
│  │                                                   │
│  ├─ API Routes (6 blueprints)                        │
│  │  /api/stocks, /api/ai, /api/agents, /api/scheduler│
│  │  /api/stream (SSE), /api/downloads                │
│  │                                                   │
│  └─ SQLite Database                                  │
│     Single-file persistent storage                   │
└──────────────────────────────────────────────────────┘
```

### 2.2 Tech Stack

**Backend**:
- Flask 3.0.0 (web framework)
- APScheduler 3.x (job scheduling)
- CrewAI 0.100+ (multi-agent orchestration)
- SQLite (embedded database)
- Python 3.10+

**Frontend**:
- Next.js 16 (App Router)
- React 18
- TypeScript (strict mode)
- Tailwind CSS
- TradingView Lightweight Charts

**AI Providers**:
- Anthropic (Claude Haiku 4.5, Sonnet 4.5, Opus 4.6)
- OpenAI (GPT-4o, GPT-4.1)
- Google (Gemini 2.5 Flash, Pro)
- xAI (Grok-4, Grok-4-Vision)

**Data Providers**:
- Polygon.io ($29-199/mo, real-time US stocks)
- Alpha Vantage (free-$49/mo, technical indicators)
- Finnhub (free-$49/mo, news + technical)
- Yahoo Finance / yfinance (free, 15-min delay, fallback)

---

## 3. Multi-Agent System

### 3.1 Agent Registry

| Agent | Model | Role | Schedule | Frequency |
|-------|-------|------|----------|-----------|
| **Scanner** | Haiku 4.5 | Scan stocks, compute technicals, rank opportunities | Market hours | Every 15 min |
| **Researcher** | Sonnet 4.5 | Generate comprehensive research briefs | On-demand manual | Variable |
| **Regime** | Sonnet 4.5 | Market regime classification (risk-on/off/neutral) | 4x daily | Every 2 hours |
| **Investigator** | Haiku 4.5 | Reddit/social media sentiment monitoring | Hourly (market hours) | 1x per hour |
| **Download Tracker** | Haiku 4.5 | GitHub repository clone statistics | Daily at 9:00 AM ET | Once daily |

### 3.2 Agent Framework Options

**CrewAI (Default)**:
- Python-native agent orchestration
- Agents defined as Python classes with tools
- Direct API calls to AI providers
- Automatic agent-to-agent collaboration via tasks

**OpenClaw (Alternative)**:
- WebSocket-based agent gateway
- Requires `OPENCLAW_GATEWAY_URL` and `OPENCLAW_WEBHOOK_TOKEN`
- Enabled via `OPENCLAW_ENABLED=true`
- Allows external agent management

### 3.3 Agent Execution Flow

```
User triggers agent manually (or scheduler triggers)
           ↓
Agent Framework (CrewAI/OpenClaw) selected
           ↓
Agent receives task + stock list
           ↓
Agent calls tools (fetch data, analyze, generate report)
           ↓
Token usage + cost tracked per agent
           ↓
Result stored in database
           ↓
SSE broadcast to all connected clients
           ↓
Frontend displays results in mission control + dashboard
```

---

## 4. Scheduler System

### 4.1 Job Categories

**Morning Routine**:
- `morning_briefing` - Regime classification + Scanner summary (8:30 AM ET)

**Technical Monitoring**:
- `technical_monitor_*` - Per-stock technical analysis (every 15 min, market hours)
- `rsi_monitor` - RSI breakout alerts (every 30 min, market hours)

**Social Media**:
- `reddit_scanner` - Scan 8 subreddits for mentions (hourly, market hours)
- `reddit_full_scan` - Comprehensive scan (daily, 3 PM ET)
- `twitter_scanner` - Twitter/X sentiment (hourly, market hours)

**Daily Reports**:
- `daily_summary` - EOD summary of events (4 PM ET)
- `download_tracker` - GitHub clone stats (9 AM ET)

**Market Analysis**:
- `regime_monitor` - Market regime classification (every 2 hours)
- `sector_rotation` - Sector strength analysis (daily, 10 AM ET)

**Extended Hours**:
- `after_hours_monitor` - Post-market technical analysis (4:15 PM ET)

### 4.2 Scheduler Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/scheduler/jobs` | GET | List all scheduled jobs with status |
| `/api/scheduler/jobs/<id>/trigger` | POST | Trigger job immediately (ignores schedule) |
| `/api/scheduler/jobs/<id>/pause` | POST | Pause recurring job |
| `/api/scheduler/jobs/<id>/resume` | POST | Resume paused job |

### 4.3 Job Execution State

- **Scheduled**: Job has next run time, waiting for trigger
- **Running**: Job currently executing
- **Paused**: Job disabled, won't run on schedule
- **Failed**: Last execution had error (with error message)

---

## 5. Data Providers System

### 5.1 Provider Priority Chain

```
Request for stock data (price, technicals, etc.)
           ↓
Try Polygon.io (if POLYGON_API_KEY set) → if success, return
           ↓
Try Alpha Vantage (if ALPHA_VANTAGE_KEY set) → if success, return
           ↓
Try Finnhub (if FINNHUB_API_KEY set) → if success, return
           ↓
Fall back to yfinance (always available) → return
```

**Key Feature**: If primary provider fails or rate-limits, next provider in chain is tried automatically. No manual intervention needed.

### 5.2 Supported Data Types per Provider

| Provider | Price | Technicals | News | Fundamentals |
|----------|-------|-----------|------|--------------|
| Polygon.io | ✅ Real-time | ✅ | ✅ | ✅ |
| Alpha Vantage | ✅ | ✅ | ❌ | ✅ |
| Finnhub | ✅ 15-min | ✅ | ✅ | ✅ |
| yfinance | ✅ 15-min delay | ✅ | ❌ | ✅ |

### 5.3 Data Source Integration (News & Social)

**Automated Feeds** (12+ sources, no API key required):
- Google News, Yahoo Finance, Seeking Alpha, MarketWatch, Benzinga
- Finviz, StockTwits, Reddit (JSON endpoints), Twitter/X (limited)

**India-Specific** (for .NS/.BO tickers):
- Economic Times, Moneycontrol, Mint

**Reddit Integration** (optional with PRAW authentication):
- 8 subreddits: r/stocks, r/investing, r/wallstreetbets, etc.
- REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET enable authenticated access

---

## 6. API Endpoints

### 6.1 Stocks Management

```http
GET /api/stocks
Response: { data: [{ticker, name, description}], meta: {...}, errors: null }

POST /api/stocks
Body: { ticker: "AAPL", name: "Apple Inc" }
Response: { data: {id, ticker, name, ...}, meta: {...}, errors: null }

DELETE /api/stocks/<ticker>
Response: { data: {deleted: true}, meta: {...}, errors: null }
```

### 6.2 AI Ratings & Analysis

```http
GET /api/ai/ratings
Response: { data: [{ticker, rating, reasoning, timestamp}], ... }

GET /api/ai/rating/<ticker>
Response: { data: {ticker, rating, reasoning, agents_used: [...]}, ... }

GET /api/news
Response: { data: [{title, source, url, published}], ... }

GET /api/alerts
Response: { data: [{type, ticker, message, severity}], ... }
```

### 6.3 Agent Management

```http
GET /api/agents
Response: { data: [{name, status, last_run, next_run, framework}], ... }

POST /api/agents/<name>/run
Body: { stocks: ["AAPL", "MSFT"], config: {...} }
Response: { data: {run_id, status, started_at}, ... }

GET /api/agents/runs
Response: { data: [{run_id, agent, status, cost_usd, duration_ms}], ... }

GET /api/agents/costs
Response: { data: {total_month: 456.78, by_agent: {...}, budget_remaining: 1043.22}, ... }
```

### 6.4 Scheduler Control

```http
GET /api/scheduler/jobs
Response: { data: [{id, name, next_run, status}], ... }

POST /api/scheduler/jobs/<id>/trigger
Response: { data: {job_id, triggered_at, status: "running"}, ... }

POST /api/scheduler/jobs/<id>/pause
POST /api/scheduler/jobs/<id>/resume
```

### 6.5 Real-Time Updates

```http
GET /api/stream
Response: Server-Sent Events (SSE) stream

Events:
- agent:started {agent, run_id, ...}
- agent:progress {agent, run_id, step, ...}
- agent:completed {agent, run_id, result, cost_usd, ...}
- stock:updated {ticker, price, change, ...}
- alert:new {type, ticker, message, ...}
```

### 6.6 Download Statistics

```http
GET /api/downloads/stats
Response: { data: {total: 15234, weekly: 1234}, ... }

GET /api/downloads/daily
Response: { data: [{date, count, cumulative}], ... }

GET /api/downloads/summary
Response: { data: {total, trend, last_7d_avg, projected_monthly}, ... }
```

### 6.7 Health & Diagnostics

```http
GET /api/health
Response: { status: "healthy", uptime_seconds: 86400, agents_running: 0 }
```

---

## 7. Database Schema

### 7.1 Core Tables

**stocks**:
- id (INTEGER PRIMARY KEY)
- ticker (TEXT UNIQUE)
- name (TEXT)
- description (TEXT)
- sector (TEXT)
- market (TEXT) - "US" or "India"
- added_at (TIMESTAMP)

**agent_runs**:
- id (INTEGER PRIMARY KEY)
- agent_name (TEXT)
- status (TEXT) - "pending", "running", "completed", "failed"
- started_at (TIMESTAMP)
- completed_at (TIMESTAMP)
- tokens_used (INTEGER)
- cost_usd (FLOAT)
- result (JSON)
- error (TEXT)

**ai_ratings**:
- id (INTEGER PRIMARY KEY)
- ticker (TEXT FOREIGN KEY)
- rating (TEXT) - "BUY", "HOLD", "SELL"
- confidence (FLOAT) - 0.0 to 1.0
- reasoning (TEXT)
- generated_by (TEXT) - agent name
- generated_at (TIMESTAMP)

**data_fetches**:
- id (INTEGER PRIMARY KEY)
- ticker (TEXT)
- provider (TEXT) - "polygon", "finnhub", "alpha_vantage", "yfinance"
- data_type (TEXT) - "price", "technical", "news"
- status (TEXT) - "success", "failed", "rate_limited"
- error (TEXT)
- fetched_at (TIMESTAMP)

**alerts**:
- id (INTEGER PRIMARY KEY)
- type (TEXT) - "rsi_breakout", "price_alert", "sentiment", "unusual_volume"
- ticker (TEXT)
- message (TEXT)
- severity (TEXT) - "info", "warning", "critical"
- created_at (TIMESTAMP)

**downloads**:
- id (INTEGER PRIMARY KEY)
- date (DATE)
- clone_count (INTEGER)
- unique_cloners (INTEGER)
- source (TEXT) - "github_api"
- tracked_at (TIMESTAMP)

### 7.2 Configuration Tables

**settings**:
- key (TEXT PRIMARY KEY)
- value (JSON)
- updated_at (TIMESTAMP)

Typical keys:
- `api_keys` - {anthropic, openai, google, xai}
- `data_providers` - {polygon, alpha_vantage, finnhub}
- `budget_config` - {monthly_limit, daily_warning}
- `agent_framework` - "crewai" or "openclaw"
- `market_timezone` - "US/Eastern" or "Asia/Kolkata"

---

## 8. Cost Management System

### 8.1 Cost Tracking

Each agent run records:
- Model used (Haiku 4.5, Sonnet 4.5, etc.)
- Tokens consumed (input + output)
- Cost calculated: (tokens_used / 1M) * model_pricing

### 8.2 Pricing Assumptions (Monthly)

| Agent | Model | Frequency | Daily | Monthly |
|-------|-------|-----------|-------|---------|
| Scanner | Haiku 4.5 | 5x/day | $8-15 | $175-330 |
| Technical Monitor | Haiku 4.5 | Every 15 min | $5-10 | $110-220 |
| Researcher | Sonnet 4.5 | On-demand | $2-5 | $44-110 |
| Regime | Sonnet 4.5 | 4x/day | $1-3 | $22-66 |
| Investigator | Haiku 4.5 | Hourly | $1-3 | $22-66 |
| Download Tracker | Haiku 4.5 | Daily | <$0.01 | <$0.30 |
| **TOTAL** | - | - | **$17-36** | **$373-792** |

### 8.3 Budget Controls

Environment variables:
- `MONTHLY_BUDGET_LIMIT=1500.0` - Hard limit, agents pause if exceeded
- `DAILY_BUDGET_WARNING=75.0` - Soft limit, warns but continues

Dashboard shows:
- Current month spending (updated real-time)
- Budget remaining (with % of limit)
- Spending trend (daily average)
- Cost per agent (for optimization)

---

## 9. Security & Configuration

### 9.1 API Keys (Optional)

All configured via `.env` or Settings UI:

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_AI_KEY=...
XAI_API_KEY=...

POLYGON_API_KEY=
ALPHA_VANTAGE_KEY=
FINNHUB_API_KEY=
TWELVE_DATA_KEY=

REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=

GITHUB_TOKEN=  # For download tracking
```

### 9.2 Flask Configuration

```
FLASK_PORT=5000
FLASK_DEBUG=false (production)
SECRET_KEY=change-this-to-random-string (session + CSRF)
```

### 9.3 Frontend Configuration

```
NEXT_PUBLIC_API_URL=http://localhost:5000
```

### 9.4 System Configuration

```
MARKET_TIMEZONE=US/Eastern  # or Asia/Kolkata for India
CHECK_INTERVAL=300  # Polling interval in seconds
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
DEFAULT_AGENT_FRAMEWORK=crewai  # or openclaw
OPENCLAW_ENABLED=false  # Enable alternative framework
OPENCLAW_GATEWAY_URL=ws://127.0.0.1:18789
OPENCLAW_WEBHOOK_TOKEN=
```

---

## 10. User Journeys

### 10.1 Retail Investor Setup & Monitoring

```
1. Install & launch (./run.sh)
2. Settings: Add API key for Claude (minimum requirement)
3. Stocks tab: Add AAPL, MSFT, TSLA (or search autocomplete)
4. Dashboard: View real-time Scanner ratings + TradingView charts
5. Mission Control: Manually trigger Researcher for deep brief on TSLA
6. Alerts: Get notified when RSI > 70 or sentiment drops
7. Budget: Monitor spending, pause agents if near limit
```

### 10.2 Active Trader Workflow

```
1. Connect premium data provider (Polygon for real-time)
2. Customize jobs: Increase Scanner frequency to 5-min, enable after-hours
3. Mission Control: Monitor Scanner runs + costs throughout day
4. Regime Monitor: Track market risk-on/off for position sizing
5. Social Integration: Enable Reddit scanner for meme stock monitoring
6. Export: Download research briefs for trade reports
```

### 10.3 Researcher Deepdive

```
1. Add 20+ stocks to portfolio
2. Trigger Researcher manually with custom questions
3. View comprehensive brief (technicals + fundamentals + sentiment)
4. Trigger Regime agent to classify market environment
5. Export brief + regime to report
```

---

## 11. Project Structure

```
tickerpulse-ai/
├── backend/
│   ├── app.py                   # Flask app factory
│   ├── config.py                # Central configuration loader
│   ├── database.py              # SQLite initialization
│   ├── scheduler.py             # APScheduler setup
│   ├── requirements.txt          # Python dependencies
│   │
│   ├── api/                      # REST API blueprints
│   │   ├── __init__.py          # Blueprint registration
│   │   ├── stocks.py            # Stock CRUD endpoints
│   │   ├── ai.py                # Ratings & analysis endpoints
│   │   ├── agents.py            # Agent control + history
│   │   ├── scheduler.py         # Job management endpoints
│   │   ├── stream.py            # SSE stream handler
│   │   └── downloads.py         # GitHub stats endpoints
│   │
│   ├── agents/                   # Multi-agent system
│   │   ├── base.py              # Agent registry + base classes
│   │   ├── crewai_engine.py     # CrewAI orchestration
│   │   ├── openclaw_engine.py   # OpenClaw WebSocket bridge
│   │   ├── scanner_agent.py     # Stock scanning agent
│   │   ├── researcher_agent.py  # Research brief generation
│   │   ├── regime_agent.py      # Market regime classification
│   │   ├── investigator_agent.py # Social media monitoring
│   │   ├── download_tracker.py  # GitHub stats agent
│   │   │
│   │   └── tools/               # CrewAI custom tools
│   │       ├── stock_tools.py   # Fetch price, technicals
│   │       ├── news_tools.py    # Scrape news feeds
│   │       ├── social_tools.py  # Reddit/Twitter sentiment
│   │       └── analysis_tools.py # Indicators, ratios
│   │
│   ├── data_providers/           # Pluggable provider chain
│   │   ├── base.py              # DataProvider ABC
│   │   ├── polygon_provider.py  # Polygon.io implementation
│   │   ├── alpha_vantage.py     # Alpha Vantage implementation
│   │   ├── finnhub_provider.py  # Finnhub implementation
│   │   └── yfinance_provider.py # Yahoo Finance fallback
│   │
│   ├── core/                     # Original TickerPulse modules
│   │   ├── indicators.py        # Technical analysis (RSI, MACD, etc.)
│   │   ├── news_scraper.py      # Feed parser + news extractor
│   │   ├── reddit_scanner.py    # Reddit sentiment analysis
│   │   └── portfolio.py         # Portfolio management
│   │
│   └── jobs/                     # Scheduled job definitions
│       ├── __init__.py          # Job registration
│       ├── morning_briefing.py  # Daily morning routine
│       ├── technical_monitor.py # Per-stock technical jobs
│       ├── social_monitor.py    # Reddit + Twitter jobs
│       ├── regime_monitor.py    # Market regime classifier
│       └── download_tracker.py  # GitHub clone tracker
│
├── frontend/                     # React/Next.js dashboard
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   │
│   ├── src/
│   │   ├── app/                 # Next.js App Router
│   │   │   ├── layout.tsx       # Root layout
│   │   │   ├── page.tsx         # Dashboard home
│   │   │   ├── stocks/          # Stock management page
│   │   │   ├── research/        # Research briefs
│   │   │   ├── mission-control/ # Agent control + history
│   │   │   ├── settings/        # Configuration UI
│   │   │   └── alerts/          # Alert management
│   │   │
│   │   ├── components/          # React components
│   │   │   ├── StockTable.tsx
│   │   │   ├── RatingCard.tsx
│   │   │   ├── AgentMissionControl.tsx
│   │   │   ├── SettingsForm.tsx
│   │   │   └── ... (chart, alert components)
│   │   │
│   │   └── lib/                 # Utilities
│   │       ├── api.ts          # Fetch wrapper + error handling
│   │       ├── hooks.ts        # Custom React hooks
│   │       └── types.ts        # TypeScript interfaces
│   │
│   └── public/                  # Static assets
│
├── templates/                   # Legacy HTML dashboard
│   ├── index.html
│   ├── dashboard.html
│   └── ...
│
├── docker-compose.yml           # Container orchestration
├── install.sh                   # Linux/macOS installer
├── install.ps1                  # Windows PowerShell installer
├── run.sh                        # Start both backend + frontend
├── stop.sh                       # Stop running services
│
├── .env.example                 # Environment template
├── README.md                    # User-facing documentation
├── CONTRIBUTING.md              # Developer guidelines
├── CLAUDE.md                    # AI development instructions
└── LICENSE                      # GPL-3.0

```

---

## 12. Key Design Patterns

### 12.1 Data Provider Chain (Strategy Pattern)

Each data request tries providers in priority order until one succeeds:
- **Fail-fast**: If provider returns error/timeout, skip to next
- **Transparent fallback**: No UI indication which provider served data
- **Cost optimization**: Expensive APIs checked before free APIs

### 12.2 Agent Registry (Registry Pattern)

All agents registered at startup:
```python
AGENT_REGISTRY = {
    "scanner": ScannerAgent(...),
    "researcher": ResearcherAgent(...),
    # ...
}
```

Allows:
- Dynamic agent discovery
- Framework-agnostic execution (CrewAI vs OpenClaw)
- Cost tracking per agent

### 12.3 SSE Broadcasting (Observer Pattern)

All connected clients receive real-time updates:
- Agent start/progress/completion
- Stock price changes
- New alerts
- No polling needed

### 12.4 Configuration Abstraction

All settings accessible via:
- Environment variables (`.env`)
- Settings UI (frontend form)
- Database (persisted across restarts)

Priority: Environment > Database > Defaults

---

## 13. Performance & Reliability

### 13.1 Caching

- Stock data cached for 60 seconds (rate limit protection)
- Agent run history cached for 1 hour
- Technical indicators cached per stock per timeframe

### 13.2 Error Handling

- Provider failures → fallback to next provider
- Agent crashes → logged + marked failed in UI
- SSE disconnects → client auto-reconnects
- Database locks → APScheduler handles gracefully

### 13.3 Monitoring

- All agent runs logged with cost + duration
- Failed jobs visible in scheduler UI with error details
- Health endpoint provides uptime + active agents
- No external logging required (file-based logs)

---

## 14. Development Workflow

### 14.1 Adding a New Agent

1. Create `backend/agents/new_agent.py` (extend BaseAgent)
2. Register in `backend/agents/base.py` AGENT_REGISTRY
3. Add job definition in `backend/jobs/` if scheduled
4. Add endpoint in `backend/api/agents.py` if manual trigger needed
5. Add frontend component in `frontend/src/components/`
6. Document in README.md

### 14.2 Adding a New Data Provider

1. Create `backend/data_providers/provider_name.py` (extend DataProvider ABC)
2. Register in provider chain in `backend/data_providers/__init__.py`
3. Add API key to `.env.example`
4. Test fallback behavior when provider unavailable

### 14.3 Adding a New API Endpoint

1. Follow REST conventions (GET list, POST create, DELETE remove)
2. Return `{data, meta, errors}` structure
3. Add endpoint to `backend/api/` blueprint
4. Register blueprint in `backend/app.py`
5. Add frontend fetch call in `frontend/src/lib/api.ts`
6. Document in README.md

---

## 15. Known Limitations & Future Work

### 15.1 Current Limitations

- Single SQLite database (not distributed)
- No built-in authentication/multi-user support
- Scheduler tied to Flask process (no external job queue)
- CrewAI framework is most tested; OpenClaw is experimental

### 15.2 Future Enhancement Ideas

- Multi-user support with role-based access
- External job queue (Redis/Celery) for scalability
- Real-time collaboration (multiple users monitoring same stocks)
- Advanced backtesting framework
- Mobile app
- Paper trading integration

---

## 16. Getting Help

**For developers**:
- See `CLAUDE.md` for development conventions
- See `CONTRIBUTING.md` for PR guidelines
- Check existing agent implementations for patterns

**For users**:
- See README.md for setup + configuration
- Settings UI guides through API key + budget setup
- Dashboard mission control shows agent execution history

---

**Remember**: TickerPulse AI is a research tool, not financial advice. All trading decisions must be human-made.
