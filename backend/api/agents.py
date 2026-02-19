"""
TickerPulse AI v3.0 - Agents API Routes
Blueprint for agent management, execution, run history, and cost tracking.

All routes delegate to the real AgentRegistry backed by the agent
implementations in backend/agents/.  Stubs and random data have been removed.
"""

import sqlite3
import threading
import logging
from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request

from backend.config import Config

logger = logging.getLogger(__name__)

agents_bp = Blueprint('agents', __name__, url_prefix='/api')

# ---------------------------------------------------------------------------
# Static display metadata for the real agents
# (fields not stored in AgentConfig but needed by the frontend)
# ---------------------------------------------------------------------------

_AGENT_METADATA = {
    'scanner': {
        'display_name': 'Stock Scanner',
        'description': (
            'Fast technical scan of all monitored stocks. Ranks by opportunity '
            'score using RSI, MACD, moving averages, and Bollinger Bands.'
        ),
        'category': 'analysis',
        'schedule': '0 * * * *',
    },
    'researcher': {
        'display_name': 'Deep Researcher',
        'description': (
            'Generates in-depth research briefs with AI-powered analysis for '
            'top opportunities and monitored stocks.'
        ),
        'category': 'research',
        'schedule': None,
    },
    'regime': {
        'display_name': 'Market Regime Analyst',
        'description': (
            'Classifies the current macro market regime (bull/bear/sideways) '
            'using macro indicators and adjusts strategy signals accordingly.'
        ),
        'category': 'analysis',
        'schedule': '0 9 * * 1-5',
    },
    'investigator': {
        'display_name': 'Social Media Investigator',
        'description': (
            'Scans Reddit and social media for retail sentiment signals on '
            'monitored stocks.'
        ),
        'category': 'analysis',
        'schedule': '*/30 * * * *',
    },
    'download_tracker': {
        'display_name': 'Download Tracker',
        'description': (
            'Tracks GitHub repository download and star metrics for tech '
            'stock research and developer adoption signals.'
        ),
        'category': 'data_collection',
        'schedule': '0 */6 * * *',
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_registry():
    """Retrieve the AgentRegistry from the app extension store."""
    try:
        return current_app.extensions.get('agent_registry')
    except RuntimeError:
        # Outside Flask app context — create via singleton getter
        from backend.agents import get_registry
        return get_registry()


def _format_agent(agent_status: dict) -> dict:
    """Merge a real agent status dict with static display metadata."""
    name = agent_status['name']
    meta = _AGENT_METADATA.get(name, {})
    return {
        'name': name,
        'display_name': meta.get('display_name', name.replace('_', ' ').title()),
        'description': meta.get('description', agent_status.get('role', '')),
        'category': meta.get('category', 'analysis'),
        'schedule': meta.get('schedule'),
        'status': agent_status.get('status', 'idle'),
        'enabled': agent_status.get('enabled', True),
        'model': agent_status.get('model', ''),
        'tags': agent_status.get('tags', []),
        'total_runs': agent_status.get('run_count', 0),
        'last_run': None,
        'total_cost': 0.0,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@agents_bp.route('/agents', methods=['GET'])
def list_agents():
    """List all registered agents with their current status.

    Query Parameters:
        category (str, optional): Filter by agent category.
        enabled (str, optional): Filter by enabled status ('true' or 'false').

    Returns:
        JSON object with:
        - agents: Array of agent summary objects.
        - total: Total count of agents returned.
    """
    category = request.args.get('category')
    enabled_filter = request.args.get('enabled')

    registry = _get_registry()
    if registry is None:
        return jsonify({'agents': [], 'total': 0})

    agents = [_format_agent(a) for a in registry.list_agents()]

    if category:
        agents = [a for a in agents if a['category'] == category]

    if enabled_filter is not None:
        enabled_bool = enabled_filter.lower() == 'true'
        agents = [a for a in agents if a['enabled'] == enabled_bool]

    # Enrich each agent with live run stats from DB
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        for agent in agents:
            row = conn.execute(
                'SELECT * FROM agent_runs WHERE agent_name = ? ORDER BY started_at DESC LIMIT 1',
                (agent['name'],)
            ).fetchone()
            if row:
                agent['last_run'] = {
                    'id': row['id'],
                    'agent_name': row['agent_name'],
                    'status': row['status'],
                    'started_at': row['started_at'],
                    'completed_at': row['completed_at'],
                    'duration_ms': row['duration_ms'] or 0,
                    'tokens_used': (row['tokens_input'] or 0) + (row['tokens_output'] or 0),
                    'estimated_cost': row['estimated_cost'] or 0,
                }
            count = conn.execute(
                'SELECT COUNT(*) FROM agent_runs WHERE agent_name = ?',
                (agent['name'],)
            ).fetchone()[0]
            agent['total_runs'] = count
            total_cost = conn.execute(
                'SELECT COALESCE(SUM(estimated_cost), 0) FROM agent_runs WHERE agent_name = ?',
                (agent['name'],)
            ).fetchone()[0]
            agent['total_cost'] = round(total_cost, 4)
        conn.close()
    except Exception as e:
        logger.error("Failed to enrich agents with run data: %s", e)

    return jsonify({'agents': agents, 'total': len(agents)})


@agents_bp.route('/agents/<name>', methods=['GET'])
def get_agent_detail(name):
    """Get detailed information about a specific agent including run history.

    Path Parameters:
        name (str): Agent identifier (e.g. 'scanner').

    Returns:
        JSON object with full agent details and a 'recent_runs' array.

    Errors:
        404: Agent not found.
        503: Registry not initialised.
    """
    registry = _get_registry()
    if registry is None:
        return jsonify({'error': 'Agent registry not initialised'}), 503

    agent_obj = registry.get(name)
    if agent_obj is None:
        return jsonify({'error': f'Agent not found: {name}'}), 404

    detail = _format_agent(agent_obj.get_status_dict())

    # Recent runs from DB
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            'SELECT * FROM agent_runs WHERE agent_name = ? ORDER BY started_at DESC LIMIT 10',
            (name,)
        ).fetchall()
        conn.close()
        detail['recent_runs'] = [{
            'id': r['id'],
            'status': r['status'],
            'started_at': r['started_at'],
            'completed_at': r['completed_at'],
            'duration_ms': r['duration_ms'] or 0,
            'tokens_used': (r['tokens_input'] or 0) + (r['tokens_output'] or 0),
            'estimated_cost': r['estimated_cost'] or 0,
            'framework': r['framework'],
        } for r in rows]
    except Exception as e:
        logger.error("Failed to fetch recent runs for %s: %s", name, e)
        detail['recent_runs'] = []

    detail['config'] = {
        'model': agent_obj.config.model,
        'max_tokens': agent_obj.config.max_tokens,
        'temperature': agent_obj.config.temperature,
        'provider': agent_obj.config.provider,
    }
    detail['tools'] = _get_agent_tools(name)

    return jsonify(detail)


@agents_bp.route('/agents/<name>/run', methods=['POST'])
def trigger_agent_run(name):
    """Manually trigger an agent run.

    Path Parameters:
        name (str): Agent identifier.

    Request Body (JSON, optional):
        params (dict): Optional parameters to pass to the agent.
            For example, {'tickers': ['AAPL', 'TSLA']} to limit scope.

    Returns:
        JSON object with:
        - success (bool): Whether the run was accepted.
        - run_id (int): Unique identifier for this run.
        - agent (str): Agent name.
        - status: 'running' (execution happens asynchronously).
        An ``agent_status`` SSE event is fired on completion.

    Errors:
        404: Agent not found.
        400: Agent is disabled.
        503: Registry not initialised.
    """
    registry = _get_registry()
    if registry is None:
        return jsonify({'error': 'Agent registry not initialised'}), 503

    agent_obj = registry.get(name)
    if agent_obj is None:
        return jsonify({'error': f'Agent not found: {name}'}), 404

    if not agent_obj.config.enabled:
        return jsonify({
            'success': False,
            'error': f'Agent "{name}" is currently disabled. Enable it in settings first.'
        }), 400

    data = request.get_json(silent=True) or {}
    params = data.get('params', {})

    # Pre-insert a 'running' row to obtain a stable run_id before the thread starts
    started_at = datetime.utcnow().isoformat() + 'Z'
    run_id = _insert_running_row(name, params, started_at)

    # Dispatch real execution in a background thread
    thread = threading.Thread(
        target=_execute_agent_async,
        args=(registry, name, params, run_id),
        daemon=True,
    )
    thread.start()

    logger.info("Agent run started: %s, run_id=%s", name, run_id)

    return jsonify({
        'success': True,
        'run_id': run_id,
        'agent': name,
        'status': 'running',
        'message': f'Agent "{name}" is now running',
        'started_at': started_at,
    })


@agents_bp.route('/agents/runs', methods=['GET'])
def list_recent_runs():
    """List recent agent runs across all agents.

    Query Parameters:
        limit (int, optional): Maximum number of runs to return. Default 50, max 200.
        agent (str, optional): Filter by agent name.
        status (str, optional): Filter by run status
            (running, success, error).

    Returns:
        JSON object with:
        - runs: Array of run summary objects.
        - total: Total count of runs returned.
    """
    limit = min(int(request.args.get('limit', 50)), 200)
    agent_filter = request.args.get('agent')
    status_filter = request.args.get('status')

    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row

        query = 'SELECT * FROM agent_runs WHERE 1=1'
        params = []

        if agent_filter:
            query += ' AND agent_name = ?'
            params.append(agent_filter)
        if status_filter:
            query += ' AND status = ?'
            params.append(status_filter)

        query += ' ORDER BY started_at DESC LIMIT ?'
        params.append(limit)

        rows = conn.execute(query, params).fetchall()
        conn.close()

        runs = [{
            'id': r['id'],
            'agent_name': r['agent_name'],
            'status': r['status'],
            'output': r['output_data'],
            'duration_ms': r['duration_ms'] or 0,
            'tokens_used': (r['tokens_input'] or 0) + (r['tokens_output'] or 0),
            'estimated_cost': r['estimated_cost'] or 0,
            'started_at': r['started_at'],
            'completed_at': r['completed_at'],
            'framework': r['framework'],
        } for r in rows]
    except Exception as e:
        logger.error("Failed to query agent runs: %s", e)
        runs = []

    return jsonify({
        'runs': runs,
        'total': len(runs),
        'filters': {
            'limit': limit,
            'agent': agent_filter,
            'status': status_filter,
        },
    })


@agents_bp.route('/agents/costs', methods=['GET'])
def get_cost_summary():
    """Get cost summary for agent runs (AI API usage).

    Query Parameters:
        period (str, optional): Aggregation period -- 'daily', 'weekly', or 'monthly'.
            Defaults to 'daily'.

    Returns:
        JSON object with cost breakdown by period and agent, plus totals.
    """
    period = request.args.get('period', 'daily')
    valid_periods = ['daily', 'weekly', 'monthly']

    if period not in valid_periods:
        return jsonify({
            'error': f'Invalid period: {period}. Must be one of: {", ".join(valid_periods)}'
        }), 400

    period_days = {'daily': 1, 'weekly': 7, 'monthly': 30}[period]
    range_labels = {'daily': 'Last 24 hours', 'weekly': 'Last 7 days', 'monthly': 'Last 30 days'}

    now = datetime.utcnow()
    range_start = (now - timedelta(days=period_days)).isoformat() + 'Z'

    registry = _get_registry()
    if registry is None:
        return jsonify({
            'period': period,
            'range_label': range_labels[period],
            'range_start': range_start,
            'range_end': now.isoformat() + 'Z',
            'total_cost_usd': 0.0,
            'total_runs': 0,
            'total_tokens': 0,
            'by_agent': {},
            'by_provider': {},
        })

    summary = registry.get_cost_summary(days=period_days)

    # Build by_agent map keyed by agent name (preserve API shape)
    by_agent = {}
    for row in summary.get('by_agent', []):
        by_agent[row['agent_name']] = {
            'display_name': _AGENT_METADATA.get(row['agent_name'], {}).get(
                'display_name', row['agent_name'].replace('_', ' ').title()
            ),
            'runs': row['runs'],
            'cost_usd': round(row['cost'], 6),
            'tokens_used': row['tokens'],
        }

    return jsonify({
        'period': period,
        'range_label': range_labels[period],
        'range_start': range_start,
        'range_end': now.isoformat() + 'Z',
        'total_cost_usd': summary.get('total_cost', 0.0),
        'total_runs': summary.get('total_runs', 0),
        'total_tokens': (
            summary.get('total_tokens_input', 0) + summary.get('total_tokens_output', 0)
        ),
        'by_agent': by_agent,
        'by_provider': {},  # future: aggregate by model provider
        'by_day': summary.get('by_day', []),
    })


# ---------------------------------------------------------------------------
# Async execution helpers
# ---------------------------------------------------------------------------

def _insert_running_row(agent_name: str, params: dict, started_at: str) -> int:
    """Insert a 'running' placeholder row and return its rowid."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.execute(
            """INSERT INTO agent_runs
               (agent_name, framework, status, input_data, started_at)
               VALUES (?, 'native', 'running', ?, ?)""",
            (agent_name, str(params) if params else None, started_at),
        )
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return run_id
    except Exception as e:
        logger.error("Failed to insert running row for %s: %s", agent_name, e)
        return 0


def _execute_agent_async(registry, agent_name: str, params: dict, run_id: int):
    """Run the agent and update the pre-inserted row when done."""
    result = _dispatch(registry, agent_name, params)

    if run_id:
        _update_run_row(run_id, result)

    # Fire SSE notification
    try:
        from backend.app import send_sse_event
        send_sse_event('agent_status', {
            'agent_name': agent_name,
            'status': result.status,
            'run_id': run_id,
            'duration_ms': result.duration_ms,
            'tokens_used': result.tokens_input + result.tokens_output,
            'estimated_cost': result.estimated_cost,
            'message': (
                f'Agent "{agent_name}" completed successfully'
                if result.status == 'success'
                else f'Agent "{agent_name}" failed: {result.error}'
            ),
        })
    except Exception as e:
        logger.warning("Failed to send SSE event for %s: %s", agent_name, e)

    logger.info(
        "Agent run finished: %s, run_id=%s, status=%s, duration=%dms",
        agent_name, run_id, result.status, result.duration_ms,
    )


def _dispatch(registry, agent_name: str, params: dict):
    """Route execution: OpenClaw (if enabled/reachable) → direct agent.run().

    Returns an AgentResult regardless of the path taken.
    The result is NOT persisted here — callers handle DB persistence
    (either by updating the pre-inserted row or via registry._persist_result).
    """
    # --- OpenClaw path ---
    if Config.OPENCLAW_ENABLED:
        try:
            from backend.agents.openclaw_engine import OpenClawBridge
            bridge = OpenClawBridge()
            if bridge.is_available():
                logger.info("Dispatching %s via OpenClaw", agent_name)
                return bridge.run_task(
                    agent_name=agent_name,
                    task_description=f"Run {agent_name} agent",
                    inputs=params or {},
                )
        except Exception as e:
            logger.warning(
                "OpenClaw dispatch failed for %s, falling back to native: %s",
                agent_name, e,
            )

    # --- Direct path: call agent.run() without re-persisting ---
    # We call agent.run() directly (not registry.run_agent()) to avoid a
    # duplicate DB write — the pre-inserted 'running' row will be UPDATEd
    # by the caller (_update_run_row).
    agent_obj = registry.get(agent_name)
    if agent_obj is not None:
        return agent_obj.run(params or {})

    # Should not be reachable, but provide a safe fallback
    from backend.agents.base import AgentResult
    return AgentResult(
        agent_name=agent_name,
        framework='native',
        status='error',
        output='',
        error=f'Agent {agent_name} not found in registry',
    )


def _update_run_row(run_id: int, result) -> None:
    """UPDATE the pre-inserted 'running' row with the final AgentResult."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.execute(
            """UPDATE agent_runs SET
               framework    = ?,
               status       = ?,
               output_data  = ?,
               tokens_input = ?,
               tokens_output = ?,
               estimated_cost = ?,
               duration_ms  = ?,
               error        = ?,
               completed_at = ?
               WHERE id = ?""",
            (
                result.framework,
                result.status,
                result.output[:10000] if result.output else None,
                result.tokens_input,
                result.tokens_output,
                result.estimated_cost,
                result.duration_ms,
                result.error,
                result.completed_at or (datetime.utcnow().isoformat() + 'Z'),
                run_id,
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error("Failed to update run row %s: %s", run_id, e)


# ---------------------------------------------------------------------------
# Agent tool metadata (informational, used by GET /api/agents/<name>)
# ---------------------------------------------------------------------------

def _get_agent_tools(agent_name: str) -> list:
    """Return the list of tools available to a given agent."""
    tool_map = {
        'scanner': [
            {'name': 'stock_data_fetcher', 'description': 'Fetches historical OHLCV price data'},
            {'name': 'technical_analyzer', 'description': 'Computes RSI, MACD, MA, Bollinger Bands, Stochastic'},
            {'name': 'news_fetcher', 'description': 'Fetches recent news for sentiment context'},
        ],
        'researcher': [
            {'name': 'stock_data_fetcher', 'description': 'Fetches historical OHLCV price data'},
            {'name': 'news_fetcher', 'description': 'Fetches news articles for research'},
            {'name': 'technical_analyzer', 'description': 'Provides technical analysis context'},
        ],
        'regime': [
            {'name': 'stock_data_fetcher', 'description': 'Fetches macro index price data'},
            {'name': 'technical_analyzer', 'description': 'Computes trend and momentum indicators'},
        ],
        'investigator': [
            {'name': 'reddit_scanner', 'description': 'Scans Reddit for stock mentions and sentiment'},
            {'name': 'news_fetcher', 'description': 'Cross-references news with social signals'},
        ],
        'download_tracker': [
            {'name': 'github_api', 'description': 'Fetches repository download and star metrics'},
        ],
    }
    return tool_map.get(agent_name, [])
