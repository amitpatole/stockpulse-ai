'use client';

import { useState } from 'react';
import { Play, Loader2, Clock, Cpu, DollarSign, Zap } from 'lucide-react';
import { clsx } from 'clsx';
import type { Agent } from '@/lib/types';
import { AGENT_STATUS_COLORS } from '@/lib/types';
import { runAgent } from '@/lib/api';

interface AgentCardProps {
  agent: Agent;
  onRunComplete?: () => void;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

function formatCost(cost: number): string {
  if (cost < 0.01) return `$${cost.toFixed(4)}`;
  return `$${cost.toFixed(2)}`;
}

function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays}d ago`;
}

export default function AgentCard({ agent, onRunComplete }: AgentCardProps) {
  const [running, setRunning] = useState(false);
  const [runError, setRunError] = useState<string | null>(null);

  const statusColor = AGENT_STATUS_COLORS[agent.status] || AGENT_STATUS_COLORS.idle;
  const isRunning = agent.status === 'running' || running;

  const handleRun = async () => {
    setRunning(true);
    setRunError(null);
    try {
      await runAgent(agent.name);
      onRunComplete?.();
    } catch (err) {
      setRunError(err instanceof Error ? err.message : 'Failed to run agent');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-slate-700/50">
            <Cpu className="h-5 w-5 text-blue-400" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white capitalize">{agent.display_name || agent.name}</h3>
            <p className="text-xs text-slate-400">{agent.description || agent.role || ''}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            role="img"
            aria-label={`Agent status: ${isRunning ? 'running' : agent.status}`}
            className={clsx('h-2.5 w-2.5 rounded-full', statusColor, isRunning && 'animate-pulse')}
          >
            <span className="sr-only">{isRunning ? 'running' : agent.status}</span>
          </span>
          <span className="text-xs text-slate-400 capitalize" aria-hidden="true">{isRunning ? 'running' : agent.status}</span>
        </div>
      </div>

      {/* Model Badge */}
      <div className="mt-3">
        <span className="inline-flex items-center gap-1 rounded-md bg-slate-700/50 px-2 py-0.5 text-xs text-slate-300">
          <Zap className="h-3 w-3 text-amber-400" />
          {agent.model || agent.category || 'AI Agent'}
        </span>
      </div>

      {/* Stats */}
      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-lg bg-slate-900/50 p-2.5">
          <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-slate-500">
            <Clock className="h-3 w-3" />
            Last Run
          </div>
          <p className="mt-0.5 text-xs font-medium text-slate-300">
            {agent.last_run?.started_at ? timeAgo(agent.last_run.started_at) : 'Never'}
          </p>
          {agent.last_run?.duration_ms != null && (
            <p className="text-[10px] text-slate-500">
              Duration: {formatDuration(agent.last_run.duration_ms)}
            </p>
          )}
        </div>

        <div className="rounded-lg bg-slate-900/50 p-2.5">
          <div className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-slate-500">
            <DollarSign className="h-3 w-3" />
            Cost
          </div>
          <p className="mt-0.5 text-xs font-medium text-slate-300 font-mono">
            {agent.total_cost != null ? formatCost(agent.total_cost) : '—'}
          </p>
          {agent.last_run?.tokens_used != null && (
            <p className="text-[10px] text-slate-500">
              {agent.last_run.tokens_used.toLocaleString()} tokens
            </p>
          )}
        </div>
      </div>

      {/* Run Count */}
      <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
        <span>Total runs: {agent.run_count ?? agent.total_runs ?? 0}</span>
        {agent.last_run?.estimated_cost != null && (
          <span className="font-mono">Last: {formatCost(agent.last_run.estimated_cost)}</span>
        )}
      </div>

      {/* Run Error */}
      {runError && (
        <div className="mt-2 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs text-red-400">
          {runError}
        </div>
      )}

      {/* Run Button */}
      <button
        onClick={handleRun}
        disabled={isRunning || !agent.enabled}
        aria-label={isRunning ? `Running ${agent.display_name || agent.name}` : `Run ${agent.display_name || agent.name}`}
        className="mt-4 flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {isRunning ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Running...
          </>
        ) : (
          <>
            <Play className="h-4 w-4" />
            Run Now
          </>
        )}
      </button>
    </div>
  );
}
