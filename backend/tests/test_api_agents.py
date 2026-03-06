"""
Comprehensive pytest test suite for Agents API endpoints.

Covers:
- List all agents with filtering
- Get agent details
- Agent execution and run history
- Cost aggregation
- Error handling and validation
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock


class TestAgentsAPI:
    """Tests for GET /api/agents and related endpoints."""

    def test_list_agents_success(self, client, mock_agents):
        """Test listing all agents returns correct structure."""
        with patch('backend.api.agents.get_all_agents', return_value=mock_agents):
            response = client.get('/api/agents')
            assert response.status_code == 200
            data = json.loads(response.data)

            assert 'data' in data
            assert isinstance(data['data'], list)
            assert len(data['data']) == 3
            assert data['data'][0]['name'] == 'research_analyst'
            assert data['data'][0]['role'] == 'Senior Research Analyst'

    def test_list_agents_empty(self, client):
        """Test listing agents when none exist."""
        with patch('backend.api.agents.get_all_agents', return_value=[]):
            response = client.get('/api/agents')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['data'] == []

    def test_list_agents_filter_by_enabled(self, client, mock_agents):
        """Test filtering agents by enabled status."""
        enabled_agents = [a for a in mock_agents if a['enabled']]
        with patch('backend.api.agents.get_agents_by_enabled', return_value=enabled_agents):
            response = client.get('/api/agents?enabled=true')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['data']) == 2
            assert all(a['enabled'] for a in data['data'])

    def test_list_agents_filter_by_disabled(self, client, mock_agents):
        """Test filtering agents by disabled status."""
        disabled_agents = [a for a in mock_agents if not a['enabled']]
        with patch('backend.api.agents.get_agents_by_enabled', return_value=disabled_agents):
            response = client.get('/api/agents?enabled=false')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['data']) == 1
            assert not data['data'][0]['enabled']

    def test_list_agents_filter_by_tag(self, client, mock_agents):
        """Test filtering agents by tag."""
        tagged_agents = [a for a in mock_agents if 'research' in a.get('tags', [])]
        with patch('backend.api.agents.get_agents_by_tag', return_value=tagged_agents):
            response = client.get('/api/agents?tag=research')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['data']) == 1
            assert 'research' in data['data'][0]['tags']

    def test_list_agents_invalid_filter(self, client):
        """Test invalid filter parameter returns error."""
        response = client.get('/api/agents?invalid_param=value')
        # Endpoint should either ignore or handle gracefully
        assert response.status_code in [200, 400]

    def test_get_agent_by_name_success(self, client, mock_agents):
        """Test getting specific agent by name."""
        agent = mock_agents[0]
        with patch('backend.api.agents.get_agent_by_name', return_value=agent):
            response = client.get('/api/agents/research_analyst')
            assert response.status_code == 200
            data = json.loads(response.data)

            assert 'data' in data
            assert data['data']['name'] == 'research_analyst'
            assert data['data']['role'] == 'Senior Research Analyst'
            assert 'goal' in data['data']
            assert 'backstory' in data['data']

    def test_get_agent_by_name_not_found(self, client):
        """Test getting non-existent agent returns 404."""
        with patch('backend.api.agents.get_agent_by_name', return_value=None):
            response = client.get('/api/agents/nonexistent_agent')
            assert response.status_code == 404
            data = json.loads(response.data)
            assert 'error' in data or 'detail' in data

    def test_get_agent_detail_with_tools(self, client, mock_agents):
        """Test agent detail includes tools and configuration."""
        agent = mock_agents[0].copy()
        agent['tools'] = [
            {'name': 'search_stocks', 'description': 'Search stock information'},
            {'name': 'analyze_fundamentals', 'description': 'Analyze company fundamentals'}
        ]

        with patch('backend.api.agents.get_agent_by_name', return_value=agent):
            response = client.get('/api/agents/research_analyst')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'tools' in data['data']
            assert len(data['data']['tools']) == 2

    def test_get_agent_empty_name(self, client):
        """Test getting agent with empty name."""
        response = client.get('/api/agents/')
        # Should either return all agents or 404
        assert response.status_code in [200, 404]


class TestAgentRunExecution:
    """Tests for POST /api/agents/<name>/run endpoint."""

    def test_run_agent_success(self, client, mock_agents):
        """Test successfully triggering agent execution."""
        run_result = {
            'agent_name': 'research_analyst',
            'status': 'success',
            'output': 'Generated research brief',
            'tokens_input': 1250,
            'tokens_output': 3420,
            'estimated_cost': 0.0342,
            'duration_ms': 3450,
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': (datetime.utcnow() + timedelta(seconds=3)).isoformat()
        }

        with patch('backend.api.agents.trigger_agent_run', return_value=run_result):
            response = client.post('/api/agents/research_analyst/run', json={})
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['agent_name'] == 'research_analyst'
            assert data['status'] == 'success'
            assert 'tokens_input' in data
            assert 'tokens_output' in data
            assert 'duration_ms' in data

    def test_run_agent_with_parameters(self, client):
        """Test running agent with custom parameters."""
        params = {
            'ticker': 'AAPL',
            'context': 'recent_earnings',
            'depth': 'detailed'
        }

        run_result = {
            'agent_name': 'research_analyst',
            'status': 'success',
            'output': 'Detailed AAPL analysis',
            'parameters': params,
            'duration_ms': 4200,
        }

        with patch('backend.api.agents.trigger_agent_run', return_value=run_result):
            response = client.post('/api/agents/research_analyst/run', json=params)
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'

    def test_run_agent_error_execution(self, client):
        """Test agent execution failure with error details."""
        run_result = {
            'agent_name': 'sentiment_analyst',
            'status': 'error',
            'output': 'Execution failed',
            'error': 'API rate limit exceeded',
            'duration_ms': 1200,
        }

        with patch('backend.api.agents.trigger_agent_run', return_value=run_result):
            response = client.post('/api/agents/sentiment_analyst/run', json={})
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'error'
            assert 'error' in data

    def test_run_agent_not_found(self, client):
        """Test running non-existent agent."""
        with patch('backend.api.agents.trigger_agent_run', side_effect=ValueError('Agent not found')):
            response = client.post('/api/agents/nonexistent/run', json={})
            assert response.status_code in [404, 400]

    def test_run_agent_timeout(self, client):
        """Test agent execution timeout."""
        run_result = {
            'agent_name': 'research_analyst',
            'status': 'error',
            'error': 'Execution timeout after 60 seconds',
            'duration_ms': 60000,
        }

        with patch('backend.api.agents.trigger_agent_run', return_value=run_result):
            response = client.post('/api/agents/research_analyst/run', json={})
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'error'
            assert 'timeout' in data['error'].lower()

    def test_run_agent_disabled(self, client):
        """Test cannot run disabled agent."""
        with patch('backend.api.agents.trigger_agent_run', side_effect=ValueError('Agent is disabled')):
            response = client.post('/api/agents/portfolio_manager/run', json={})
            assert response.status_code in [400, 403]

    def test_run_agent_malformed_json(self, client):
        """Test POST with malformed JSON."""
        response = client.post(
            '/api/agents/research_analyst/run',
            data='invalid json',
            content_type='application/json'
        )
        assert response.status_code in [400, 422]

    def test_run_agent_missing_content_type(self, client):
        """Test POST without Content-Type header."""
        response = client.post(
            '/api/agents/research_analyst/run',
            data='{}',
            content_type='text/plain'
        )
        assert response.status_code in [400, 415]


class TestAgentRunHistory:
    """Tests for GET /api/agents/runs endpoint."""

    def test_get_agent_runs_default_limit(self, client, mock_agent_runs):
        """Test listing agent runs with default pagination."""
        with patch('backend.api.agents.get_agent_runs', return_value=mock_agent_runs[:2]):
            response = client.get('/api/agents/runs')
            assert response.status_code == 200
            data = json.loads(response.data)

            assert 'data' in data
            assert len(data['data']) == 2

    def test_get_agent_runs_with_limit(self, client, mock_agent_runs):
        """Test listing agent runs with custom limit."""
        with patch('backend.api.agents.get_agent_runs', return_value=mock_agent_runs[:1]):
            response = client.get('/api/agents/runs?limit=1')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['data']) == 1

    def test_get_agent_runs_max_limit(self, client, mock_agent_runs):
        """Test max limit enforcement (default 50, max 200)."""
        with patch('backend.api.agents.get_agent_runs', return_value=mock_agent_runs):
            response = client.get('/api/agents/runs?limit=300')
            # Should cap at max (200) or return 422
            assert response.status_code in [200, 422]

    def test_get_agent_runs_filter_by_agent(self, client, mock_agent_runs):
        """Test filtering runs by agent name."""
        analyst_runs = [r for r in mock_agent_runs if r['agent_name'] == 'research_analyst']
        with patch('backend.api.agents.get_agent_runs', return_value=analyst_runs):
            response = client.get('/api/agents/runs?agent=research_analyst')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['data']) == 2
            assert all(r['agent_name'] == 'research_analyst' for r in data['data'])

    def test_get_agent_runs_filter_by_status(self, client, mock_agent_runs):
        """Test filtering runs by status."""
        success_runs = [r for r in mock_agent_runs if r['status'] == 'success']
        with patch('backend.api.agents.get_agent_runs', return_value=success_runs):
            response = client.get('/api/agents/runs?status=success')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert all(r['status'] == 'success' for r in data['data'])

    def test_get_agent_runs_filter_by_status_error(self, client, mock_agent_runs):
        """Test filtering for error runs."""
        error_runs = [r for r in mock_agent_runs if r['status'] == 'error']
        with patch('backend.api.agents.get_agent_runs', return_value=error_runs):
            response = client.get('/api/agents/runs?status=error')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert all(r['status'] == 'error' for r in data['data'])

    def test_get_agent_runs_empty(self, client):
        """Test listing when no runs exist."""
        with patch('backend.api.agents.get_agent_runs', return_value=[]):
            response = client.get('/api/agents/runs')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['data'] == []

    def test_get_agent_runs_invalid_limit(self, client):
        """Test invalid limit parameter."""
        response = client.get('/api/agents/runs?limit=0')
        assert response.status_code in [200, 422]

    def test_get_agent_runs_invalid_status(self, client):
        """Test invalid status filter."""
        response = client.get('/api/agents/runs?status=invalid_status')
        # Should either ignore or return 422
        assert response.status_code in [200, 422]


class TestAgentCostAggregation:
    """Tests for GET /api/agents/costs endpoint."""

    def test_get_agent_costs_all_time(self, client):
        """Test total cost aggregation across all runs."""
        cost_data = {
            'period': 'all_time',
            'total_cost': 1250.45,
            'total_runs': 342,
            'average_cost_per_run': 3.66,
            'cost_by_agent': {
                'research_analyst': 520.30,
                'sentiment_analyst': 450.15,
                'portfolio_manager': 280.00
            }
        }

        with patch('backend.api.agents.get_cost_aggregation', return_value=cost_data):
            response = client.get('/api/agents/costs')
            assert response.status_code == 200
            data = json.loads(response.data)

            assert data['period'] == 'all_time'
            assert data['total_cost'] == 1250.45
            assert 'cost_by_agent' in data

    def test_get_agent_costs_daily(self, client):
        """Test daily cost aggregation."""
        cost_data = {
            'period': 'daily',
            'date': '2025-03-03',
            'total_cost': 45.23,
            'total_runs': 12,
            'cost_by_agent': {
                'research_analyst': 25.10,
                'sentiment_analyst': 20.13
            }
        }

        with patch('backend.api.agents.get_cost_aggregation', return_value=cost_data):
            response = client.get('/api/agents/costs?period=daily')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['period'] == 'daily'
            assert 'date' in data

    def test_get_agent_costs_weekly(self, client):
        """Test weekly cost aggregation."""
        cost_data = {
            'period': 'weekly',
            'week_starting': '2025-02-24',
            'total_cost': 312.45,
            'total_runs': 87,
            'cost_by_agent': {}
        }

        with patch('backend.api.agents.get_cost_aggregation', return_value=cost_data):
            response = client.get('/api/agents/costs?period=weekly')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['period'] == 'weekly'

    def test_get_agent_costs_monthly(self, client):
        """Test monthly cost aggregation."""
        cost_data = {
            'period': 'monthly',
            'month': '2025-03',
            'total_cost': 1850.75,
            'total_runs': 420,
            'cost_by_agent': {}
        }

        with patch('backend.api.agents.get_cost_aggregation', return_value=cost_data):
            response = client.get('/api/agents/costs?period=monthly')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['period'] == 'monthly'

    def test_get_agent_costs_invalid_period(self, client):
        """Test invalid period parameter."""
        response = client.get('/api/agents/costs?period=invalid')
        # Should either default or return 422
        assert response.status_code in [200, 422]

    def test_get_agent_costs_by_provider(self, client):
        """Test cost aggregation by AI provider."""
        cost_data = {
            'breakdown': 'by_provider',
            'cost_by_provider': {
                'anthropic': 850.25,
                'openai': 200.50
            },
            'total_cost': 1050.75
        }

        with patch('backend.api.agents.get_cost_aggregation', return_value=cost_data):
            response = client.get('/api/agents/costs?breakdown=by_provider')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'cost_by_provider' in data

    def test_get_agent_costs_zero_runs(self, client):
        """Test cost aggregation when no runs exist."""
        cost_data = {
            'period': 'daily',
            'total_cost': 0.0,
            'total_runs': 0,
            'cost_by_agent': {}
        }

        with patch('backend.api.agents.get_cost_aggregation', return_value=cost_data):
            response = client.get('/api/agents/costs?period=daily')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['total_cost'] == 0.0
            assert data['total_runs'] == 0


class TestAgentAPIErrorHandling:
    """Tests for error handling in Agents API."""

    def test_internal_server_error(self, client):
        """Test handling of internal server errors."""
        with patch('backend.api.agents.get_all_agents', side_effect=Exception('Database error')):
            response = client.get('/api/agents')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data or 'detail' in data

    def test_database_connection_error(self, client):
        """Test database connection failure."""
        with patch('backend.api.agents.get_all_agents', side_effect=ConnectionError('DB unavailable')):
            response = client.get('/api/agents')
            assert response.status_code in [500, 503]

    def test_api_rate_limit_error(self, client):
        """Test API provider rate limit error."""
        with patch('backend.api.agents.trigger_agent_run', side_effect=Exception('Rate limit exceeded')):
            response = client.post('/api/agents/research_analyst/run', json={})
            assert response.status_code in [429, 500]

    def test_invalid_agent_config(self, client):
        """Test invalid agent configuration."""
        with patch('backend.api.agents.get_agent_by_name', side_effect=ValueError('Invalid config')):
            response = client.get('/api/agents/bad_config')
            assert response.status_code in [400, 500]

    def test_concurrent_agent_runs(self, client):
        """Test handling concurrent run requests for same agent."""
        with patch('backend.api.agents.trigger_agent_run') as mock_run:
            mock_run.side_effect = Exception('Agent already running')
            response = client.post('/api/agents/research_analyst/run', json={})
            assert response.status_code in [400, 409, 500]
