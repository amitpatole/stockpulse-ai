/**
 * AgentCard Component Tests
 *
 * Tests for the AgentCard component which displays AI agent information,
 * metrics, and provides a "Run Now" button to execute the agent.
 *
 * Coverage:
 * - Rendering with complete and partial agent data
 * - Run functionality (success and failure cases)
 * - Status display and animations
 * - Formatting helpers (duration, cost, time ago)
 * - Error handling and loading states
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AgentCard from '../AgentCard';
import type { Agent } from '@/lib/types';
import { server } from '@/__tests__/setup';
import { http, HttpResponse } from 'msw';

/**
 * AC1: AgentCard displays agent metadata (name, status, model, cost, runs)
 * AC2: Run Now button triggers agent execution with loading state
 * AC3: Errors from API are caught and displayed to user
 * AC4: Time/cost formatting is human-readable
 */

describe('AgentCard', () => {
  /**
   * HAPPY PATH: Render complete agent with all metrics
   */
  it('should render agent with complete metadata', () => {
    const agent: Agent = {
      id: '1',
      name: 'sentiment_analyzer',
      display_name: 'Sentiment Analyzer',
      description: 'Analyzes market sentiment from news',
      status: 'idle',
      enabled: true,
      model: 'gpt-4',
      category: 'analysis',
      role: 'analyzer',
      total_cost: 12.45,
      run_count: 5,
      total_runs: 5,
      last_run: {
        started_at: new Date(Date.now() - 60000).toISOString(), // 1 minute ago
        duration_ms: 5000,
        tokens_used: 2500,
        estimated_cost: 0.05,
      },
    };

    render(<AgentCard agent={agent} />);

    // Verify metadata displayed
    expect(screen.getByText('Sentiment Analyzer')).toBeInTheDocument();
    expect(screen.getByText('Analyzes market sentiment from news')).toBeInTheDocument();
    expect(screen.getByText('gpt-4')).toBeInTheDocument();

    // Verify metrics displayed with formatting
    expect(screen.getByText('Total runs: 5')).toBeInTheDocument();
    expect(screen.getByText('1m ago')).toBeInTheDocument(); // timeAgo formatting
    expect(screen.getByText('Duration: 5.0s')).toBeInTheDocument(); // formatDuration
    expect(screen.getByText(/\$0\.05/)).toBeInTheDocument(); // formatCost
    expect(screen.getByText(/2,500 tokens/)).toBeInTheDocument();
  });

  /**
   * HAPPY PATH: Run agent successfully
   */
  it('should run agent on button click and call onRunComplete', async () => {
    const onRunComplete = vi.fn();
    const agent: Agent = {
      id: '1',
      name: 'test_agent',
      status: 'idle',
      enabled: true,
      total_runs: 0,
    };

    // Mock the runAgent API call
    server.use(
      http.post('http://localhost:8000/api/agents/test_agent/run', () => {
        return HttpResponse.json({ data: { success: true } });
      })
    );

    render(<AgentCard agent={agent} onRunComplete={onRunComplete} />);

    const runButton = screen.getByRole('button', { name: /Run Now/i });
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(onRunComplete).toHaveBeenCalledOnce();
    });
  });

  /**
   * ERROR CASE: API fails when running agent
   */
  it('should display error message when run fails', async () => {
    const agent: Agent = {
      id: '1',
      name: 'failing_agent',
      status: 'idle',
      enabled: true,
    };

    // Mock API failure
    server.use(
      http.post('http://localhost:8000/api/agents/failing_agent/run', () => {
        return HttpResponse.json(
          { error: 'Agent execution failed' },
          { status: 500 }
        );
      })
    );

    render(<AgentCard agent={agent} />);

    const runButton = screen.getByRole('button', { name: /Run Now/i });
    fireEvent.click(runButton);

    await waitFor(() => {
      expect(screen.getByText(/Failed to run agent/i)).toBeInTheDocument();
    });
  });

  /**
   * EDGE CASE: Agent with missing optional fields
   */
  it('should render gracefully with minimal agent data', () => {
    const agent: Agent = {
      id: '1',
      name: 'minimal_agent',
      status: 'idle',
      enabled: true,
      // No description, model, last_run, costs
    };

    render(<AgentCard agent={agent} />);

    expect(screen.getByText('minimal_agent')).toBeInTheDocument();
    expect(screen.getByText('idle')).toBeInTheDocument();
    expect(screen.getByText('Total runs: 0')).toBeInTheDocument();
    expect(screen.getByText('Never')).toBeInTheDocument(); // No last_run
    expect(screen.getByText('—')).toBeInTheDocument(); // No cost
  });

  /**
   * EDGE CASE: Disable button when agent is not enabled
   */
  it('should disable run button when agent is not enabled', () => {
    const agent: Agent = {
      id: '1',
      name: 'disabled_agent',
      status: 'idle',
      enabled: false,
    };

    render(<AgentCard agent={agent} />);

    const runButton = screen.getByRole('button', { name: /Run Now/i });
    expect(runButton).toBeDisabled();
  });

  /**
   * EDGE CASE: Show running state when agent status is 'running'
   */
  it('should show running state when agent status is running', () => {
    const agent: Agent = {
      id: '1',
      name: 'running_agent',
      status: 'running',
      enabled: true,
    };

    render(<AgentCard agent={agent} />);

    // Status should show "running"
    expect(screen.getByText('running')).toBeInTheDocument();

    // Run button should be disabled
    const runButton = screen.getByRole('button', { name: /Running\.\.\./i });
    expect(runButton).toBeDisabled();
  });

  /**
   * EDGE CASE: Format cost with 4 decimal places for small amounts
   */
  it('should format costs correctly for different amounts', () => {
    const smallCostAgent: Agent = {
      id: '1',
      name: 'small_cost',
      status: 'idle',
      enabled: true,
      total_cost: 0.0025,
    };

    const largeCostAgent: Agent = {
      id: '2',
      name: 'large_cost',
      status: 'idle',
      enabled: true,
      total_cost: 125.50,
    };

    const { rerender } = render(<AgentCard agent={smallCostAgent} />);
    expect(screen.getByText('$0.0025')).toBeInTheDocument();

    rerender(<AgentCard agent={largeCostAgent} />);
    expect(screen.getByText('$125.50')).toBeInTheDocument();
  });
});
