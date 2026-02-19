"""
TickerPulse AI v3.0 - Agents API Routes
Blueprint for agent management, execution, run history, and cost tracking.

Routes delegate to the module-level AgentRegistry singleton (initialised in
create_app via backend.agents.init_registry).  No stub data; all metrics
are produced by real agent runs.
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import sqlite3
import logging

from backend.config import Config
from backend.agents import get_registry
from backend.agents.base import BaseAgent

logger = logging.getLogger(__name__)

agents_bp = Blueprint('agents', __name__, url_prefix='/api')

# ---------------------------------------------------------------------------
# Category map: agent name → API category string
# ---------------------------------------------------------------------------

_CATEGORY_MAP: dict[str, str] = {
    'scanner': 'analysis',
    'researcher': 'research',
    'regime': 'analysis',
    'investigator': 'monitoring',
    'download_tracker': 'data_collection',
}


def _to_api_dict(agent: BaseAgent) -> dict:
    """Map a BaseAgent to the response shape expected by the frontend.

    ``get_status_dict()`` returns role/model/tags; this function adds the
    display_name/description/category fields the dashboard relies on.
    """
    cfg = agent.config
    category = _CATEGORY_MAP.get(cfg.name, cfg.tags[0] if cfg.tags else 'general')
    return {
        'name': cfg.name,
        'display_name': cfg.role,
        'description': cfg.goal,
        'category': category,
        'schedule': None,
        'status': agent.status.value,
        'enabled': cfg.enabled,
        'model': cfg.model,
        'tags': cfg.tags,
        # DB-enriched fields populated by the route
        'last_run': None,
        'avg_duration_seconds': None,
        'total_runs': 0,
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
    category = request.args.get('category', None)
    enabled_filter = request.args.get('enabled', None)

    registry = get_registry()
    agents = []
    for status_dict in registry.list_agents():
        agent = registry.get(status_dict['name'])
        if agent:
            agents.append(_to_api_dict(agent))

    if category:
        agents = [a for a in agents if a['category'] == category]

    if enabled_filter is not None:
        enabled_bool = enabled_filter.lower() == 'true'
        agents = [a for a in agents if a['enabled'] == enabled_bool]

    # Enrich with last_run data from DB
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
        logger.error(f"Failed to enrich agents with run data: {e}")

    return jsonify({
        'agents': agents,
        'total': len(agents)
    })


@agents_bp.route('/agents/<name>', methods=['GET'])
def get_agent_detail(name):
    """Get detailed information about a specific agent including run history.

    Path Parameters:
        name (str): Agent identifier (e.g. 'scanner').

    Returns:
        JSON object with full agent details and a 'recent_runs' array.

    Errors:
        404: Agent not found.
    """
    registry = get_registry()
    agent = registry.get(name)
    if not agent:
        return jsonify({'error': f'Agent not found: {name}'}), 404

    detail = _to_api_dict(agent)
    detail['recent_runs'] = registry.get_run_history(agent_name=name, limit=10)
    detail['config'] = {
        'model': agent.config.model,
        'max_tokens': agent.config.max_tokens,
        'temperature': agent.config.temperature,
        'provider': agent.config.provider,
    }
    detail['tools'] = []

    return jsonify(detail)


@agents_bp.route('/agents/<name>/run', methods=['POST'])
def trigger_agent_run(name):
    """Manually trigger an agent run.

    Path Parameters:
        name (str): Agent identifier.

    Request Body (JSON, optional):
        params (dict): Parameters passed to the agent
            (e.g. {'ticker': 'AAPL'} for the researcher).

    Returns:
        JSON object with real duration_ms, token counts, cost, and output.

    Errors:
        404: Agent not found.
        400: Agent is disabled.
        503: Missing dependency or API key.
    """
    registry = get_registry()
    agent = registry.get(name)
    if not agent:
        return jsonify({'error': f'Agent not found: {name}'}), 404

    if not agent.config.enabled:
        return jsonify({
            'success': False,
            'error': f'Agent "{name}" is currently disabled. Enable it in settings first.'
        }), 400

    data = request.get_json(silent=True) or {}
    inputs = data.get('params', {})

    # Run agent synchronously; registry persists the result to DB
    result = registry.run_agent(name, inputs)

    if result is None:
        return jsonify({'error': f'Agent not found: {name}'}), 404

    if result.status == 'error':
        error_msg = result.error or 'Agent execution failed'
        # Surface missing dependency / config errors as 503
        dependency_keywords = ('CrewAI', 'crewai', 'API key', 'ANTHROPIC_API_KEY', 'ImportError')
        if any(kw in error_msg for kw in dependency_keywords):
            return jsonify({
                'success': False,
                'error': error_msg,
                'message': (
                    'Agent could not run due to a missing dependency or configuration. '
                    'Check API keys and installed packages.'
                ),
            }), 503

    # Retrieve the run_id assigned by the DB insert in _persist_result
    run_id = None
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        row = conn.execute(
            'SELECT id FROM agent_runs WHERE agent_name = ? ORDER BY id DESC LIMIT 1',
            (name,)
        ).fetchone()
        conn.close()
        if row:
            run_id = row[0]
    except Exception as e:
        logger.error(f"Failed to fetch run_id: {e}")

    # SSE notification
    try:
        from backend.app import send_sse_event
        send_sse_event('agent_status', {
            'agent_name': name,
            'status': result.status,
            'run_id': run_id,
            'message': f'Agent "{agent.config.role}" completed with status: {result.status}',
        })
    except Exception:
        pass

    logger.info(
        "Agent run completed: %s, run_id=%s, duration=%dms, status=%s",
        name, run_id, result.duration_ms, result.status,
    )

    return jsonify({
        'success': result.status == 'success',
        'run_id': run_id,
        'agent': name,
        'status': result.status,
        'duration_ms': result.duration_ms,
        'tokens_input': result.tokens_input,
        'tokens_output': result.tokens_output,
        'estimated_cost': result.estimated_cost,
        'output': result.output,
        'error': result.error,
        'started_at': result.started_at,
        'completed_at': result.completed_at,
        'message': f'Agent "{agent.config.role}" completed with status: {result.status}',
    })


@agents_bp.route('/agents/runs', methods=['GET'])
def list_recent_runs():
    """List recent agent runs across all agents.

    Query Parameters:
        limit (int, optional): Maximum number of runs to return. Default 50, max 200.
        agent (str, optional): Filter by agent name.
        status (str, optional): Filter by run status (queued, running, completed, failed).

    Returns:
        JSON object with:
        - runs: Array of run summary objects.
        - total: Total count of runs returned.
    """
    limit = min(int(request.args.get('limit', 50)), 200)
    agent_filter = request.args.get('agent', None)
    status_filter = request.args.get('status', None)

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
        } for r in rows]
    except Exception as e:
        logger.error(f"Failed to query agent runs: {e}")
        runs = []

    return jsonify({
        'runs': runs,
        'total': len(runs),
        'filters': {
            'limit': limit,
            'agent': agent_filter,
            'status': status_filter
        }
    })


@agents_bp.route('/agents/costs', methods=['GET'])
def get_cost_summary():
    """Get cost summary for agent runs (AI API usage).

    Query Parameters:
        period (str, optional): Aggregation period -- 'daily', 'weekly', or 'monthly'.
            Defaults to 'daily'.

    Returns:
        JSON object with real cost breakdown from the agent_runs table.
    """
    period = request.args.get('period', 'daily')
    valid_periods = ['daily', 'weekly', 'monthly']

    if period not in valid_periods:
        return jsonify({
            'error': f'Invalid period: {period}. Must be one of: {", ".join(valid_periods)}'
        }), 400

    period_days = {'daily': 1, 'weekly': 7, 'monthly': 30}[period]
    range_labels = {'daily': 'Last 24 hours', 'weekly': 'Last 7 days', 'monthly': 'Last 30 days'}

    registry = get_registry()
    summary = registry.get_cost_summary(days=period_days)

    now = datetime.utcnow()
    return jsonify({
        'period': period,
        'range_label': range_labels[period],
        'range_start': (now - timedelta(days=period_days)).isoformat() + 'Z',
        'range_end': now.isoformat() + 'Z',
        'total_cost_usd': summary['total_cost'],
        'total_runs': summary['total_runs'],
        'total_tokens': summary['total_tokens_input'] + summary['total_tokens_output'],
        'by_agent': {
            row['agent_name']: {
                'runs': row['runs'],
                'cost_usd': row['cost'],
                'tokens_used': row['tokens'],
            }
            for row in summary['by_agent']
        },
        'by_day': summary['by_day'],
        'by_provider': {},
    })
