# Contributing to TickerPulse AI

Thanks for your interest in contributing to TickerPulse AI! This guide covers what you need to get started.

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- Git

## Local Development Setup

### Backend

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

pip install -r backend/requirements.txt

cp .env.example .env
# Edit .env and add at least one AI provider API key

cd backend
python app.py
# API at http://localhost:5000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Dashboard at http://localhost:3000
```

### Both (quick start)

```bash
./run.sh
```

## Project Structure

```
tickerpulse-ai/
├── backend/           # Python Flask backend
│   ├── api/           # REST API route blueprints
│   ├── agents/        # Multi-agent system (CrewAI / OpenClaw)
│   ├── core/          # Core modules (AI providers, stock manager, etc.)
│   ├── data_providers/# Pluggable stock data providers
│   └── jobs/          # Scheduled job definitions
├── frontend/          # React/Next.js dashboard
├── electron/          # Electron desktop wrapper
└── templates/         # Legacy HTML dashboard
```

## Making Changes

1. Fork the repository and create a branch from `main`.
2. Make your changes in a focused, single-purpose branch.
3. Test your changes locally (backend + frontend).
4. Submit a pull request.

### Coding Conventions

**Python (backend)**
- Follow PEP 8.
- Use type hints where practical.
- Keep Flask blueprints to one file per domain (stocks, news, agents, etc.).
- Data providers and agents follow the ABC + Registry pattern — see `data_providers/base.py` and `agents/base.py`.

**TypeScript/React (frontend)**
- Use functional components with hooks.
- Keep components in `frontend/src/components/`.
- Use the existing API client patterns in `frontend/src/lib/`.

**Electron**
- Main process code lives in `electron/main/`.
- Preload scripts in `electron/preload/`.
- The bridge object is `window.tickerpulse`.

### Commit Messages

- Use concise, descriptive messages that explain *why* not *what*.
- Examples: `Fix agent_runs schema migration for v3.0.0 upgrades`, `Add auto-update via electron-updater`.

### Pull Requests

- Keep PRs focused — one feature or fix per PR.
- Include a short description of what changed and why.
- Reference any related issues.

## Adding a Data Provider

TickerPulse AI uses a pluggable data provider system. To add a new provider:

1. Create a new file in `backend/data_providers/` (e.g., `my_provider.py`).
2. Subclass `DataProvider` from `backend/data_providers/base.py`.
3. Implement the required abstract methods.
4. Register the provider in the provider registry.

See `yfinance_provider.py` for a reference implementation.

## Adding an Agent

1. Create a new file in `backend/agents/` (e.g., `my_agent.py`).
2. Subclass the base agent class from `backend/agents/base.py`.
3. Register the agent in `backend/agents/__init__.py`.

See `scanner_agent.py` for a reference implementation.

## Important Notes

- TickerPulse AI is a **research and monitoring tool**. It does not execute trades or provide financial advice. Contributions should not add trade execution functionality.
- Do not commit API keys, credentials, or `.env` files.
- Database files (`*.db`, `*.sqlite`) are gitignored — do not commit them.

## License

By contributing, you agree that your contributions will be licensed under the [GNU General Public License v3.0 (GPL-3.0)](LICENSE).

All contributions must include attribution to the original project and maintain the GPL-3.0 license headers where applicable.

## Questions?

Open an issue on [GitHub](https://github.com/amitpatole/tickerpulse-ai/issues) for questions, bug reports, or feature requests.
