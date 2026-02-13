'use client';

import { useState } from 'react';
import {
  Play,
  Pause,
  RotateCw,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  Calendar,
  AlertTriangle,
} from 'lucide-react';
import { clsx } from 'clsx';
import Header from '@/components/layout/Header';
import { useApi } from '@/hooks/useApi';
import { getSchedulerJobs, triggerJob, pauseJob, resumeJob, getAgentRuns } from '@/lib/api';
import type { ScheduledJob, AgentRun } from '@/lib/types';

function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return 'N/A';
  const date = new Date(dateStr);
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

export default function SchedulerPage() {
  const [refreshKey, setRefreshKey] = useState(0);
  const [actionLoading, setActionLoading] = useState<Record<string, string>>({});

  const { data: jobs, loading: jobsLoading, error: jobsError, refetch: refetchJobs } = useApi<ScheduledJob[]>(
    getSchedulerJobs,
    [refreshKey],
    { refreshInterval: 15000 }
  );

  const { data: runs } = useApi<AgentRun[]>(
    () => getAgentRuns(20),
    [refreshKey],
    { refreshInterval: 30000 }
  );

  const handleAction = async (jobId: string, action: 'trigger' | 'pause' | 'resume') => {
    setActionLoading((prev) => ({ ...prev, [jobId]: action }));
    try {
      switch (action) {
        case 'trigger':
          await triggerJob(jobId);
          break;
        case 'pause':
          await pauseJob(jobId);
          break;
        case 'resume':
          await resumeJob(jobId);
          break;
      }
      setRefreshKey((k) => k + 1);
      refetchJobs();
    } catch {
      // Error handling is silent for now
    } finally {
      setActionLoading((prev) => {
        const next = { ...prev };
        delete next[jobId];
        return next;
      });
    }
  };

  return (
    <div className="flex flex-col">
      <Header title="Job Scheduler" subtitle="Manage scheduled tasks and automation" />

      <div className="flex-1 p-6">
        {/* Jobs Table */}
        <div className="mb-6 rounded-xl border border-slate-700/50 bg-slate-800/50">
          <div className="border-b border-slate-700/50 px-4 py-3">
            <h2 className="text-sm font-semibold text-white">Scheduled Jobs</h2>
          </div>

          {jobsLoading && !jobs && (
            <div className="p-6 text-center text-sm text-slate-500">Loading jobs...</div>
          )}

          {jobsError && !jobs && (
            <div className="p-6 text-center">
              <AlertTriangle className="mx-auto h-6 w-6 text-red-400" />
              <p className="mt-2 text-sm text-red-400">{jobsError}</p>
            </div>
          )}

          {jobs && jobs.length === 0 && (
            <div className="p-6 text-center text-sm text-slate-500">No scheduled jobs found.</div>
          )}

          {jobs && jobs.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400">Job</th>
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400">Schedule</th>
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400">Next Run</th>
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400">Last Run</th>
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400">Status</th>
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/30">
                  {jobs.map((job) => {
                    const isLoading = !!actionLoading[job.id];
                    const currentAction = actionLoading[job.id];

                    return (
                      <tr key={job.id} className="transition-colors hover:bg-slate-700/20">
                        <td className="px-4 py-3">
                          <div>
                            <p className="font-medium text-white">{job.name}</p>
                            <p className="text-xs text-slate-500">{job.description}</p>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className="rounded bg-slate-700 px-2 py-0.5 text-xs text-slate-300 font-mono">
                            {job.trigger}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-slate-300">
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3 text-slate-500" />
                            <span className="text-xs">{formatDate(job.next_run)}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-400">{formatDate(job.last_run)}</td>
                        <td className="px-4 py-3">
                          <span
                            className={clsx(
                              'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
                              job.enabled
                                ? 'bg-emerald-500/10 text-emerald-400'
                                : 'bg-slate-500/10 text-slate-400'
                            )}
                          >
                            <span className={clsx('h-1.5 w-1.5 rounded-full', job.enabled ? 'bg-emerald-500' : 'bg-slate-500')} />
                            {job.enabled ? 'Active' : 'Paused'}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-1.5">
                            {/* Trigger */}
                            <button
                              onClick={() => handleAction(job.id, 'trigger')}
                              disabled={isLoading}
                              className="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-blue-500/20 hover:text-blue-400 disabled:opacity-50"
                              title="Trigger now"
                            >
                              {currentAction === 'trigger' ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <Play className="h-4 w-4" />
                              )}
                            </button>

                            {/* Pause/Resume */}
                            {job.enabled ? (
                              <button
                                onClick={() => handleAction(job.id, 'pause')}
                                disabled={isLoading}
                                className="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-amber-500/20 hover:text-amber-400 disabled:opacity-50"
                                title="Pause"
                              >
                                {currentAction === 'pause' ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Pause className="h-4 w-4" />
                                )}
                              </button>
                            ) : (
                              <button
                                onClick={() => handleAction(job.id, 'resume')}
                                disabled={isLoading}
                                className="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-emerald-500/20 hover:text-emerald-400 disabled:opacity-50"
                                title="Resume"
                              >
                                {currentAction === 'resume' ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <RotateCw className="h-4 w-4" />
                                )}
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Recent Job Executions */}
        <div className="rounded-xl border border-slate-700/50 bg-slate-800/50">
          <div className="border-b border-slate-700/50 px-4 py-3">
            <h2 className="text-sm font-semibold text-white">Recent Executions</h2>
          </div>

          {runs && runs.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-slate-700/50">
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400">Agent</th>
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400">Status</th>
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400">Duration</th>
                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-400">Started</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/30">
                  {runs.map((run, idx) => (
                    <tr key={run.id ?? idx} className="transition-colors hover:bg-slate-700/20">
                      <td className="px-4 py-3 font-medium text-white capitalize">{run.agent_name}</td>
                      <td className="px-4 py-3">
                        <span
                          className={clsx(
                            'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium',
                            run.status === 'completed'
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : run.status === 'running'
                              ? 'bg-blue-500/10 text-blue-400'
                              : 'bg-red-500/10 text-red-400'
                          )}
                        >
                          {run.status === 'completed' ? (
                            <CheckCircle className="h-3 w-3" />
                          ) : run.status === 'running' ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <XCircle className="h-3 w-3" />
                          )}
                          {run.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-mono text-slate-300">{formatDuration(run.duration_ms)}</td>
                      <td className="px-4 py-3 text-slate-400">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          <span className="text-xs">{formatDate(run.started_at)}</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-6 text-center text-sm text-slate-500">No recent executions.</div>
          )}
        </div>
      </div>
    </div>
  );
}
