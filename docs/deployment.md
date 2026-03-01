# TickerPulse AI v3.0 — Production Deployment Guide

This guide covers all supported deployment methods: Docker Compose (recommended), bare-metal, and reverse-proxy configuration.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Docker Compose Deployment (Recommended)](#docker-compose-deployment-recommended)
4. [Bare-Metal Deployment](#bare-metal-deployment)
5. [Reverse Proxy Setup](#reverse-proxy-setup)
6. [Post-Deployment Verification](#post-deployment-verification)
7. [Operational Runbook](#operational-runbook)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Hardware minimums

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 2 GB | 4 GB |
| Disk | 10 GB | 20 GB |

### Software

| Dependency | Minimum Version | Notes |
|------------|----------------|-------|
| Docker | 24.x | Required for Docker deployment |
| Docker Compose | 2.x (`docker compose`) | Bundled with Docker Desktop |
| Python | 3.10+ | Required for bare-metal |
| Node.js | 18+ | Required for bare-metal |
| npm | 9+ | Required for bare-metal |
| git | Any | Required to clone the repository |

---

## Environment Configuration

### 1. Copy the example environment file

```bash
cp .env.example .env
```

### 2. Required settings

Edit `.env` and set **at minimum** one AI provider key and a strong secret key:

```env
# Must change — used for session signing
SECRET_KEY=<random-64-char-string>

# At least one AI provider key is required
ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
# GOOGLE_AI_KEY=...
# XAI_API_KEY=...
```

Generate a strong secret key:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Full environment reference

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `tickerpulse-dev-key-change-in-prod` | **Required in production** — Flask session signing key |
| `FLASK_PORT` | `5000` | Backend listening port |
| `FLASK_DEBUG` | `false` | Must be `false` in production |
| `DB_PATH` | `stock_news.db` | SQLite database path |
| `DB_POOL_SIZE` | `5` | Number of pooled DB connections |
| `DB_POOL_TIMEOUT` | `10.0` | Seconds to wait for a free connection |
| `CORS_ORIGINS` | `http://localhost:3000,...` | Comma-separated allowed origins |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT_JSON` | `false` | Set `true` for structured JSON logs |
| `LOG_DIR` | `logs/` | Log file directory |
| `MARKET_TIMEZONE` | `US/Eastern` | Timezone for market-hour scheduling |
| `CHECK_INTERVAL` | `300` | Price check interval in seconds |
| `MONTHLY_BUDGET_LIMIT` | `1500.0` | AI spend hard cap (USD) |
| `DAILY_BUDGET_WARNING` | `75.0` | Daily spend warning threshold (USD) |
| `DEFAULT_AGENT_FRAMEWORK` | `crewai` | `crewai` or `openclaw` |
| `ANTHROPIC_API_KEY` | — | Anthropic Claude |
| `OPENAI_API_KEY` | — | OpenAI GPT |
| `GOOGLE_AI_KEY` | — | Google Gemini |
| `XAI_API_KEY` | — | xAI Grok |
| `POLYGON_API_KEY` | — | Polygon.io market data |
| `ALPHA_VANTAGE_KEY` | — | Alpha Vantage market data |
| `FINNHUB_API_KEY` | — | Finnhub market data |
| `TWELVE_DATA_KEY` | — | Twelve Data market data |
| `REDDIT_CLIENT_ID` | — | Reddit PRAW (optional) |
| `REDDIT_CLIENT_SECRET` | — | Reddit PRAW (optional) |
| `GITHUB_TOKEN` | — | GitHub repo analytics (optional) |
| `OPENCLAW_ENABLED` | `false` | Enable OpenClaw agent gateway |
| `OPENCLAW_GATEWAY_URL` | `ws://127.0.0.1:18789` | OpenClaw WebSocket URL |
| `OPENCLAW_WEBHOOK_TOKEN` | — | OpenClaw authentication token |
| `PRICE_REFRESH_INTERVAL_SECONDS` | `30` | WebSocket price broadcast interval |
| `WS_MAX_SUBSCRIPTIONS_PER_CLIENT` | `50` | Max tickers per WebSocket client |
| `RATE_LIMIT_DEFAULT` | `60/minute` | Default API rate limit |
| `RATE_LIMIT_AI` | `20/minute` | AI endpoint rate limit |
| `RATE_LIMIT_DATA` | `30/minute` | Data endpoint rate limit |
| `NEXT_PUBLIC_API_URL` | `http://localhost:5000` | Backend URL seen by the frontend |

---

## Docker Compose Deployment (Recommended)

Docker Compose is the simplest path to a reproducible production deployment.

### Step 1 — Clone and configure

```bash
git clone https://github.com/amitpatole/tickerpulse-ai.git
cd tickerpulse-ai
cp .env.example .env
# Edit .env with production values (SECRET_KEY + at least one AI key)
```

### Step 2 — Build and start

```bash
docker compose up -d --build
```

This builds two images:

- `tickerpulse-backend` — Python 3.12 Flask API on port `5000`
- `tickerpulse-frontend` — Node.js 22 Next.js dashboard on port `3000`

The frontend waits for the backend health check (`/api/health`) to pass before starting.

### Step 3 — Verify containers are running

```bash
docker compose ps
docker compose logs backend --tail 50
docker compose logs frontend --tail 20
```

Expected output from `docker compose ps`:

```
NAME                    STATUS          PORTS
tickerpulse-backend     Up (healthy)    0.0.0.0:5000->5000/tcp
tickerpulse-frontend    Up              0.0.0.0:3000->3000/tcp
```

### Persistent data

The backend stores the SQLite database and logs in the named volume `tickerpulse-data` mounted at `/app/data` inside the container. This volume persists across container restarts and upgrades.

```bash
# Inspect volume location on host
docker volume inspect tickerpulse_tickerpulse-data
```

### Upgrading

```bash
git pull
docker compose up -d --build
```

Docker Compose pulls the latest code, rebuilds images, and performs a rolling restart with zero configuration loss (the data volume is preserved).

### Stopping

```bash
docker compose down          # stop and remove containers (data volume preserved)
docker compose down -v       # stop and delete data volume (DESTRUCTIVE)
```

---

## Bare-Metal Deployment

Use this method when you cannot run Docker or need direct process control.

### Step 1 — Clone and install

```bash
git clone https://github.com/amitpatole/tickerpulse-ai.git
cd tickerpulse-ai
bash install.sh
```

The installer creates a `venv/`, installs Python and Node dependencies, builds the Next.js app, and copies `.env.example` → `.env`.

### Step 2 — Configure environment

```bash
# Edit .env with production values
nano .env
```

Set `SECRET_KEY`, at least one AI provider key, and configure `CORS_ORIGINS` to match your domain:

```env
SECRET_KEY=<64-char-random-string>
ANTHROPIC_API_KEY=sk-ant-...
CORS_ORIGINS=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
FLASK_DEBUG=false
LOG_LEVEL=INFO
```

### Step 3 — Start the application

```bash
./run.sh
```

This starts:
- Flask backend on port `5000` (logs to `logs/backend.log`)
- Next.js frontend on port `3000` (logs to `logs/frontend.log`)

Both processes run in the background via `nohup`.

### Step 4 — Confirm it is running

```bash
curl -s http://localhost:5000/api/health | python3 -m json.tool
```

Expected response:

```json
{
  "status": "ok",
  "version": "3.0"
}
```

### Running as a systemd service (recommended for bare-metal)

Create `/etc/systemd/system/tickerpulse-backend.service`:

```ini
[Unit]
Description=TickerPulse AI Backend
After=network.target

[Service]
Type=simple
User=tickerpulse
WorkingDirectory=/opt/tickerpulse-ai
EnvironmentFile=/opt/tickerpulse-ai/.env
ExecStart=/opt/tickerpulse-ai/venv/bin/python -m backend.app
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/tickerpulse-frontend.service`:

```ini
[Unit]
Description=TickerPulse AI Frontend
After=tickerpulse-backend.service

[Service]
Type=simple
User=tickerpulse
WorkingDirectory=/opt/tickerpulse-ai/frontend
ExecStart=/usr/bin/npm run start
Restart=on-failure
RestartSec=10
Environment=NODE_ENV=production
EnvironmentFile=/opt/tickerpulse-ai/.env
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable tickerpulse-backend tickerpulse-frontend
sudo systemctl start tickerpulse-backend tickerpulse-frontend
sudo systemctl status tickerpulse-backend tickerpulse-frontend
```

View logs:

```bash
sudo journalctl -u tickerpulse-backend -f
sudo journalctl -u tickerpulse-frontend -f
```

---

## Reverse Proxy Setup

In production, serve both the frontend and the backend API through a single HTTPS reverse proxy. This avoids CORS issues and allows you to use a single domain with a single TLS certificate.

### nginx

Install nginx (`apt install nginx`) then create `/etc/nginx/sites-available/tickerpulse`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate     /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Frontend (Next.js)
    location / {
        proxy_pass         http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
    }

    # Backend API — includes SSE and WebSocket
    location /api/ {
        proxy_pass         http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;

        # Required for SSE (Server-Sent Events) — disable buffering
        proxy_buffering    off;
        proxy_cache        off;
        proxy_read_timeout 3600s;
    }

    # WebSocket endpoint
    location /ws {
        proxy_pass         http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "Upgrade";
        proxy_set_header   Host $host;
        proxy_read_timeout 3600s;
    }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/tickerpulse /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### TLS certificate via Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

Certbot auto-renews; verify with:

```bash
sudo certbot renew --dry-run
```

### Environment update after reverse proxy

Once HTTPS is in place, update `.env`:

```env
CORS_ORIGINS=https://yourdomain.com
NEXT_PUBLIC_API_URL=https://yourdomain.com/api
```

Then restart both services (or rebuild and redeploy containers).

---

## Post-Deployment Verification

Run the following checks after every deployment.

### 1. Health endpoint

```bash
curl -s https://yourdomain.com/api/health | python3 -m json.tool
```

Expected: `"status": "ok"` with no `"degraded"` subsystems.

### 2. Frontend loads

Open `https://yourdomain.com` in a browser. The dashboard should load and display the stock watchlist.

### 3. SSE stream is active

```bash
curl -N https://yourdomain.com/api/stream
# Should emit periodic "heartbeat" events without blocking
# Press Ctrl+C to stop
```

### 4. Agent system

From the Settings page or via the API, trigger the Scanner agent manually:

```bash
curl -X POST https://yourdomain.com/api/agents/scanner/run \
     -H "Content-Type: application/json"
```

Expected: `202 Accepted` with a run ID.

### 5. Scheduled jobs

```bash
curl -s https://yourdomain.com/api/scheduler/jobs | python3 -m json.tool
```

All jobs should appear with a `next_run_time` field.

### 6. Database is writable (Docker)

```bash
docker exec tickerpulse-backend python3 -c "
from backend.database import get_pool; p = get_pool(); s = p.stats(); print(s)
"
```

Expected: `{'size': 5, 'available': 5, 'in_use': 0, ...}`

---

## Operational Runbook

### Viewing logs

**Docker:**

```bash
docker compose logs -f backend    # Flask API
docker compose logs -f frontend   # Next.js
```

**Bare-metal / systemd:**

```bash
sudo journalctl -u tickerpulse-backend -f
tail -f logs/backend.log
```

### Stopping the application

**Docker:**

```bash
docker compose down
```

**Bare-metal:**

```bash
./stop.sh
```

### Restarting after a configuration change

**Docker:**

```bash
docker compose down && docker compose up -d
```

**Bare-metal:**

```bash
./stop.sh && ./run.sh
```

**systemd:**

```bash
sudo systemctl restart tickerpulse-backend tickerpulse-frontend
```

### Backing up the database

**Docker (copy from named volume):**

```bash
docker run --rm \
  -v tickerpulse_tickerpulse-data:/data \
  -v $(pwd)/backups:/backup \
  alpine sh -c "cp /data/stock_news.db /backup/stock_news_$(date +%Y%m%d_%H%M%S).db"
```

**Bare-metal:**

```bash
mkdir -p backups
cp stock_news.db backups/stock_news_$(date +%Y%m%d_%H%M%S).db
```

Schedule a nightly backup with cron:

```cron
0 2 * * * /bin/cp /opt/tickerpulse-ai/stock_news.db \
  /opt/tickerpulse-ai/backups/stock_news_$(date +\%Y\%m\%d).db
```

### Rotating logs

The backend automatically rotates log files when they reach 10 MB (configurable via `LOG_MAX_BYTES`) and keeps 5 backups (`LOG_BACKUP_COUNT`). No external log rotation configuration is needed.

For structured log aggregation (e.g., Loki, Elasticsearch), set `LOG_FORMAT_JSON=true` to emit newline-delimited JSON.

---

## Troubleshooting

### Backend fails to start

**Symptom:** `docker compose ps` shows the backend as `Exited` or health check fails.

**Steps:**

```bash
docker compose logs backend --tail 100
```

Common causes:

| Error message | Fix |
|--------------|-----|
| `SECRET_KEY` not set | Add `SECRET_KEY` to `.env` |
| `DB pool exhausted` | Increase `DB_POOL_SIZE` in `.env` |
| `ModuleNotFoundError` | Run `pip install -r backend/requirements.txt` (bare-metal) or rebuild the image |
| `Address already in use` | Port 5000 is taken — change `FLASK_PORT` or kill the conflicting process |

### Frontend cannot reach the API

**Symptom:** Dashboard loads but shows API errors or empty data.

**Steps:**

1. Confirm `NEXT_PUBLIC_API_URL` in `.env` matches the backend's public URL.
2. Check `CORS_ORIGINS` includes the frontend origin exactly (no trailing slash).
3. For Docker: verify the frontend container starts **after** the backend passes its health check.

```bash
docker compose logs frontend | grep -i error
```

### SSE stream disconnects frequently

The SSE `/api/stream` endpoint uses long-lived HTTP connections. Ensure:

- nginx: `proxy_read_timeout 3600s;` and `proxy_buffering off;` are set (see Reverse Proxy section).
- Load balancers (AWS ALB, Cloudflare): set idle timeout to at least 3600 seconds.

### Agents not running on schedule

1. Check the scheduler is alive:

   ```bash
   curl -s http://localhost:5000/api/scheduler/jobs | python3 -m json.tool
   ```

2. Confirm at least one AI provider API key is configured (agents require a provider to execute).

3. Check cost limits — if `MONTHLY_BUDGET_LIMIT` is exceeded, agents are paused.

### High memory usage

The DB connection pool keeps `DB_POOL_SIZE` SQLite connections open permanently. Under heavy load, reduce to `DB_POOL_SIZE=3` or increase server RAM.

### Database locked errors

SQLite WAL mode is enabled by default. If you see `database is locked` errors:

- Ensure only one process writes to the database at a time (do not run multiple backend processes against the same file).
- For multi-process deployments, migrate to PostgreSQL via a compatible adapter.