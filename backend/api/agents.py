"""
TickerPulse AI v3.0 - Agents API Routes
Blueprint for agent management, execution, run history, and cost tracking.

Routes delegate to the real AgentRegistry (backend/agents/) rather than
generating synthetic stub data.  A stable stub→real name mapping layer
(AGENT_ID_MAP) preserves frontend-facing names while routing to the five
real agent classes.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import sqlite3
import logging

from backend.config import Config

logger = logging.getLogger(__name__)

agents_bp = Blueprint('agents', __name__, url_prefix='/api')

# ---------------------------------------------------------------------------
# Stub-to-real agent name mapping.
# The frontend uses stub names; the registry uses the real names below.
# ---------------------------------------------------------------------------

AGENT_ID_MAP: dict = {
    'sentiment_analyst':  'investigator',
    'technical_analyst':  'scanner',
    'news_scanner':       'scanner',
    'risk_monitor':       'regime',
    'report_generator':   'researcher',
    'researcher':         'researcher',
    'download_tracker':   'download_tracker',
}

# Display metadata for each frontend-visible stub ID.
_STUB_META: dict = {
    'sentiment_analyst': {
        'display_name': 'Sentiment Analyst',
        'description': 'Analyzes news and social media sentiment for monitored stocks',
        'category': 'analysis',
        'schedule': '*/30 * * * *',
    },
    'technical_analyst': {
        'display_name': 'Technical Analyst',
        'description': 'Runs technical indicator analysis (RSI, MACD, moving averages) across watchlist',
        'category': 'analysis',
        'schedule': '0 * * * *',
    },
    'news_scanner': {
        'display_name': 'News Scanner',
        'description': 'Scans multiple news sources for articles about monitored stocks',
        'category': 'data_collection',
        'schedule': '*/15 * * * *',
    },
    'risk_monitor': {
        'display_name': 'Risk Monitor',
        'description': 'Monitors portfolio risk metrics and generates alerts on threshold breaches',
        'category': 'monitoring',
        'schedule': '*/10 * * * *',
    },
    'report_generator': {
        'display_name': 'Report Generator',
        'description': 'Generates daily and weekly summary reports of market activity',
        'category': 'reporting',
        'schedule': '0 18 * * *',
    },
    'researcher': {
        'display_name': 'Deep Researcher',
        'description': 'Generates in-depth research briefs with AI-powered analysis',
        'category': 'research',
        'schedule': None,
    },
    'download_tracker': {
        'display_name': 'Download Tracker',
        'description': 'Tracks GitHub repository clone and download statistics',
        'category': 'monitoring',
        'schedule': '0 */6 * * *',
    },
}

# ---------------------------------------------------------------------------
# Registry accessor — replaced in tests to inject a mock registry.
# ---------------------------------------------------------------------------

def _get_registry():
    """Return the shared AgentRegistry, initialising it lazily if needed."""
    from backend.agents import get_registry
    return get_registry()


def _get_latest_run_id(agent_name: str) -> int:
    """Return the DB row id of the most recent run for the given real agent name."""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        row = conn.execute(
            'SELECT id FROM agent_runs WHERE agent_name = ? ORDER BY created_at DESC LIMIT 1',
            (agent_name,)
        ).fetchone()
        conn.close()
        return row[0] if row else 0
    except Exception:
        return 0


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@agents_bp.route('/agents', methods=['GET'])
def list_agents():
    """List all registered agents with their current status.

    Query Parameters:
        category (str, optional): Filter by agent category
            (analysis, data_collection, monitoring, reporting, research).
        enabled (str, optional): Filter by enabled status ('true' or 'false').

    Returns:
        JSON object with:
        - agents: Array of agent summary objects.
        - total: Total count of agents returned.
    """
    category = request.args.get('category', None)
    enabled_filter = request.args.get('enabled', None)

    registry = _get_registry()

    # Build a lookup: real_name → status dict from registry
    real_agents = {}
    for entry in registry.list_agents():
        if isinstance(entry, dict) and 'name' in entry:
            real_agents[entry['name']] = entry

    # Build the stub-facing list from _STUB_META
    agents = []
    for stub_name, meta in _STUB_META.items():
        real_name = AGENT_ID_MAP[stub_name]
        real = real_agents.get(real_name, {})

        entry = {
            'name': stub_name,
            'display_name': meta['display_name'],
            'description': meta['description'],
            'category': meta['category'],
            'schedule': meta['schedule'],
            'status': real.get('status', 'idle'),
            'enabled': real.get('enabled', True),
            'last_run': None,
            'avg_duration_seconds': None,
            'total_runs': 0,
            'total_cost': 0.0,
        }
        agents.append(entry)

    # Apply filters
    if category:
        agents = [a for a in agents if a['category'] == category]
    if enabled_filter is not None:
        enabled_bool = enabled_filter.lower() == 'true'
        agents = [a for a in agents if a['enabled'] == enabled_bool]

    # Enrich with live run stats from DB
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        for agent in agents:
            real_name = AGENT_ID_MAP[agent['name']]
            row = conn.execute(
                'SELECT * FROM agent_runs WHERE agent_name = ? ORDER BY started_at DESC LIMIT 1',
                (real_name,)
            ).fetchone()
            if row:
                agent['last_run'] = {
                    'id': row['id'],
                    'agent_name': agent['name'],
                    'status': row['status'],
                    'started_at': row['started_at'],
                    'completed_at': row['completed_at'],
                    'duration_ms': row['duration_ms'] or 0,
                    'tokens_used': (row['tokens_input'] or 0) + (row['tokens_output'] or 0),
                    'estimated_cost': row['estimated_cost'] or 0,
                }
            count = conn.execute(
                'SELECT COUNT(*) FROM agent_runs WHERE agent_name = ?',
                (real_name,)
            ).fetchone()[0]
            agent['total_runs'] = count
            total_cost = conn.execute(
                'SELECT COALESCE(SUM(estimated_cost), 0) FROM agent_runs WHERE agent_name = ?',
                (real_name,)
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
        name (str): Agent stub identifier (e.g. 'technical_analyst').

    Returns:
        JSON object with full agent details and a 'recent_runs' array.

    Errors:
        404: Agent not found.
    """
    if name not in AGENT_ID_MAP:
        return jsonify({'error': f'Agent not found: {name}'}), 404

    real_name = AGENT_ID_MAP[name]
    registry = _get_registry()
    agent = registry.get(real_name)

    if not agent:
        return jsonify({'error': f'Agent not found: {name}'}), 404

    meta = _STUB_META[name]
    status_val = agent.status.value if hasattr(agent.status, 'value') else str(agent.status)

    detail = {
        'name': name,
        'display_name': meta['display_name'],
        'description': meta['description'],
        'category': meta['category'],
        'schedule': meta['schedule'],
        'status': status_val,
        'enabled': agent.config.enabled,
        'recent_runs': [],
        'config': {
            'model': agent.config.model,
            'max_retries': 3,
            'timeout_seconds': 300,
            'concurrency': 1,
        },
        'tools': _get_agent_tools(name),
    }

    # Enrich with recent runs from DB
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            'SELECT * FROM agent_runs WHERE agent_name = ? ORDER BY started_at DESC LIMIT 10',
            (real_name,)
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
        } for r in rows]
    except Exception as e:
        logger.error("Failed to fetch run history for %s: %s", name, e)

    return jsonify(detail)


@agents_bp.route('/agents/<name>/run', methods=['POST'])
def trigger_agent_run(name):
    """Manually trigger an agent run and return the full result synchronously.

    Path Parameters:
        name (str): Agent stub identifier.

    Request Body (JSON, optional):
        params (dict): Optional parameters to pass to the agent.
            For example, {'tickers': ['AAPL', 'TSLA']} to limit scope.

    Returns:
        JSON object with:
        - success (bool): Whether the run succeeded.
        - run_id (int): DB row id for this run.
        - agent (str): Stub agent name as provided by the caller.
        - status: 'completed' or 'error'.
        - framework (str): Execution framework used (from AgentResult).
        - tokens_input / tokens_output / estimated_cost: real values from AgentResult.

    Errors:
        404: Agent not found.
        400: Agent is disabled.
    """
    if name not in AGENT_ID_MAP:
        return jsonify({'error': f'Agent not found: {name}'}), 404

    real_name = AGENT_ID_MAP[name]
    registry = _get_registry()
    agent = registry.get(real_name)

    if not agent:
        return jsonify({'error': f'Agent not found: {name}'}), 404

    if not agent.config.enabled:
        return jsonify({
            'success': False,
            'error': f'Agent "{name}" is currently disabled. Enable it in settings first.'
        }), 400

    data = request.get_json(silent=True) or {}
    params = data.get('params', {})

    # Dispatch: OpenClaw → CrewAI → native registry
    result = _dispatch_agent(real_name, params, registry)

    run_id = _get_latest_run_id(real_name)
    is_success = result.status == 'success'
    display_name = _STUB_META[name]['display_name']

    # Broadcast SSE notification
    try:
        from backend.app import send_sse_event
        send_sse_event('agent_status', {
            'agent_name': name,
            'status': result.status,
            'run_id': run_id,
            'message': (
                f'Agent "{display_name}" completed successfully'
                if is_success
                else f'Agent "{display_name}" encountered an error'
            ),
        })
    except Exception:
        pass

    logger.info(
        "Agent run: %s→%s, run_id=%s, status=%s, duration=%dms",
        name, real_name, run_id, result.status, result.duration_ms,
    )

    response: dict = {
        'success': is_success,
        'run_id': run_id,
        'agent': name,
        'status': 'completed' if is_success else 'error',
        'framework': result.framework,
        'duration_ms': result.duration_ms,
        'tokens_input': result.tokens_input,
        'tokens_output': result.tokens_output,
        'estimated_cost': result.estimated_cost,
        'completed_at': result.completed_at,
    }

    if not is_success:
        response['error'] = result.error

    return jsonify(response)


@agents_bp.route('/agents/runs', methods=['GET'])
def list_recent_runs():
    """List recent agent runs across all agents.

    Query Parameters:
        limit (int, optional): Maximum number of runs to return. Default 50, max 200.
        agent (str, optional): Filter by agent name (stub or real name accepted).
        status (str, optional): Filter by run status (running, success, error).

    Returns:
        JSON object with:
        - runs: Array of run summary objects.
        - total: Total count of runs returned.
    """
    limit = min(int(request.args.get('limit', 50)), 200)
    agent_filter = request.args.get('agent', None)
    status_filter = request.args.get('status', None)

    # Resolve stub → real agent name for DB query
    agent_filter_real = AGENT_ID_MAP.get(agent_filter, agent_filter) if agent_filter else None

    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row

        query = 'SELECT * FROM agent_runs WHERE 1=1'
        params = []

        if agent_filter_real:
            query += ' AND agent_name = ?'
            params.append(agent_filter_real)
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

    period_to_days = {'daily': 1, 'weekly': 7, 'monthly': 30}
    days = period_to_days[period]

    now = datetime.utcnow()
    if period == 'daily':
        range_start = (now - timedelta(days=1)).isoformat() + 'Z'
        range_label = 'Last 24 hours'
    elif period == 'weekly':
        range_start = (now - timedelta(weeks=1)).isoformat() + 'Z'
        range_label = 'Last 7 days'
    else:
        range_start = (now - timedelta(days=30)).isoformat() + 'Z'
        range_label = 'Last 30 days'

    registry = _get_registry()
    summary = registry.get_cost_summary(days=days)

    # Build reverse map: real_name → list of stub names
    real_to_stubs: dict = {}
    for stub, real in AGENT_ID_MAP.items():
        real_to_stubs.setdefault(real, []).append(stub)

    # Initialise by_agent with all stubs at zero so the frontend always has
    # every key regardless of whether any runs have occurred.
    by_agent: dict = {
        stub_name: {
            'display_name': meta['display_name'],
            'runs': 0,
            'cost_usd': 0.0,
            'tokens_used': 0,
        }
        for stub_name, meta in _STUB_META.items()
    }

    # Populate with real data from the registry cost summary
    for agent_row in summary.get('by_agent', []):
        real_name = agent_row.get('agent_name', '')
        for stub_name in real_to_stubs.get(real_name, []):
            if stub_name in by_agent:
                by_agent[stub_name].update({
                    'runs': agent_row.get('runs', 0),
                    'cost_usd': round(agent_row.get('cost', 0.0), 4),
                    'tokens_used': agent_row.get('tokens', 0),
                })

    return jsonify({
        'period': period,
        'range_label': range_label,
        'range_start': range_start,
        'range_end': now.isoformat() + 'Z',
        'total_cost_usd': summary.get('total_cost', 0.0),
        'total_runs': summary.get('total_runs', 0),
        'total_tokens': (
            summary.get('total_tokens_input', 0) + summary.get('total_tokens_output', 0)
        ),
        'by_agent': by_agent,
        'by_provider': {},
    })


# ---------------------------------------------------------------------------
# Dispatch helper: OpenClaw → CrewAI → native registry
# ---------------------------------------------------------------------------

def _dispatch_agent(real_name: str, params: dict, registry) -> 'AgentResult':
    """Try OpenClaw, then CrewAI, then fall back to native registry dispatch.

    All three paths return an AgentResult with real token counts, costs,
    and duration — never random placeholder values.
    """
    from backend.agents.base import AgentResult

    # 1. OpenClaw (external gateway, if enabled and reachable)
    if Config.OPENCLAW_ENABLED:
        try:
            from backend.agents.openclaw_engine import OpenClawBridge
            bridge = OpenClawBridge()
            if bridge.is_available():
                logger.info("Dispatching %s via OpenClaw", real_name)
                result = bridge.run_task(real_name, f'Execute {real_name} analysis', params)
                if result:
                    # Persist via registry since OpenClaw bypasses registry.run_agent()
                    registry._persist_result(result, params)
                    return result
        except Exception as e:
            logger.debug("OpenClaw dispatch skipped for %s: %s", real_name, e)

    # 2. CrewAI (local orchestration, if installed)
    try:
        from backend.agents.crewai_engine import TickerPulseCrewEngine, CREWAI_AVAILABLE
        if CREWAI_AVAILABLE:
            engine = TickerPulseCrewEngine()
            agent_obj = registry.get(real_name)
            if agent_obj:
                engine.register_agent_config(agent_obj.config)
                result = engine.run_crew(
                    [real_name],
                    f'Execute {real_name} agent task',
                    params,
                )
                if result:
                    registry._persist_result(result, params)
                    return result
    except Exception as e:
        logger.debug("CrewAI dispatch skipped for %s: %s", real_name, e)

    # 3. Native registry dispatch (always available)
    result = registry.run_agent(real_name, params)
    if result is None:
        result = AgentResult(
            agent_name=real_name,
            framework='native',
            status='error',
            output='',
            error='Agent execution returned no result',
        )
    return result


# ---------------------------------------------------------------------------
# Agent tool metadata (informational, used by GET /api/agents/<name>)
# ---------------------------------------------------------------------------

def _get_agent_tools(stub_name: str) -> list:
    """Return the list of tools available to a given stub agent."""
    tool_map = {
        'sentiment_analyst': [
            {'name': 'reddit_scanner', 'description': 'Scans Reddit for stock mentions and sentiment'},
            {'name': 'news_fetcher', 'description': 'Fetches news articles from configured sources'},
        ],
        'technical_analyst': [
            {'name': 'stock_data_fetcher', 'description': 'Fetches historical price and volume data'},
            {'name': 'technical_analyzer', 'description': 'Computes RSI, MACD, moving averages, Bollinger Bands'},
        ],
        'news_scanner': [
            {'name': 'news_fetcher', 'description': 'Fetches news articles from configured sources'},
            {'name': 'stock_data_fetcher', 'description': 'Fetches historical price and volume data'},
        ],
        'risk_monitor': [
            {'name': 'stock_data_fetcher', 'description': 'Fetches market instrument data'},
            {'name': 'technical_analyzer', 'description': 'Computes cross-asset technical signals'},
        ],
        'report_generator': [
            {'name': 'stock_data_fetcher', 'description': 'Fetches historical price data'},
            {'name': 'news_fetcher', 'description': 'Fetches recent news articles'},
            {'name': 'reddit_scanner', 'description': 'Scans Reddit for stock sentiment'},
            {'name': 'technical_analyzer', 'description': 'Computes technical indicators'},
        ],
        'researcher': [
            {'name': 'stock_data_fetcher', 'description': 'Fetches historical price data'},
            {'name': 'news_fetcher', 'description': 'Fetches recent news articles'},
            {'name': 'reddit_scanner', 'description': 'Scans Reddit for stock sentiment'},
            {'name': 'technical_analyzer', 'description': 'Computes technical indicators'},
        ],
        'download_tracker': [
            {'name': 'github_api', 'description': 'Fetches repository clone and traffic statistics'},
        ],
    }
    return tool_map.get(stub_name, [])
