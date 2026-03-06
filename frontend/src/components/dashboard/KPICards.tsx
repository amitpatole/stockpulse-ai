```typescript
'use client';

import { BarChart3, Bell, Activity, TrendingUp } from 'lucide-react';
import { useApi } from '@/hooks/useApi';
import { getStocks, getAlerts, getAgents } from '@/lib/api';
import type { Stock, Alert, Agent } from '@/lib/types';

interface KPICardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
  loading?: boolean;
  headingLevel?: 'h2' | 'h3';
}

function KPICard({ title, value, subtitle, icon, color, loading, headingLevel = 'h2' }: KPICardProps) {
  const HeadingTag = headingLevel;
  const headingId = `kpi-${title.toLowerCase().replace(/\s+/g, '-')}`;

  return (
    <section
      className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
      role="region"
      aria-labelledby={headingId}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <HeadingTag id={headingId} className="text-xs font-medium uppercase tracking-wider text-slate-400">
            {title}
          </HeadingTag>
          {loading ? (
            <div className="mt-2 h-8 w-20 animate-pulse rounded bg-slate-700" />
          ) : (
            <p className="mt-1 text-2xl font-bold text-white font-mono">{value}</p>
          )}
          {subtitle && !loading && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
        </div>
        <div className={`rounded-lg p-2.5 ${color}`} aria-hidden="true">
          {icon}
        </div>
      </div>
    </section>
  );
}

export default function KPICards() {
  const { data: stocks, loading: stocksLoading } = useApi<Stock[]>(getStocks, [], { refreshInterval: 30000 });
  const { data: alerts, loading: alertsLoading } = useApi<Alert[]>(getAlerts, [], { refreshInterval: 15000 });
  const { data: agents, loading: agentsLoading } = useApi<Agent[]>(getAgents, [], { refreshInterval: 10000 });

  const totalStocks = stocks?.filter((s) => s.active)?.length ?? 0;
  const activeAlerts = alerts?.length ?? 0;

  const agentCounts =
    agents?.reduce(
      (acc, a) => {
        if (a.status === 'running') acc.running++;
        else if (a.status === 'error') acc.error++;
        else acc.idle++;
        return acc;
      },
      { running: 0, idle: 0, error: 0 }
    ) ?? { running: 0, idle: 0, error: 0 };

  const agentStatusText = `${agentCounts.running} running, ${agentCounts.idle} idle${agentCounts.error > 0 ? `, ${agentCounts.error} error` : ''}`;

  return (
    <section aria-label="Key Performance Indicators" className="space-y-4">
      <h2 className="sr-only">Dashboard KPI Summary</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KPICard
          title="Stocks Monitored"
          value={totalStocks}
          subtitle={`${stocks?.length ?? 0} total tracked`}
          icon={<BarChart3 className="h-5 w-5 text-blue-400" />}
          color="bg-blue-500/10"
          loading={stocksLoading}
          headingLevel="h3"
        />
        <KPICard
          title="Active Alerts"
          value={activeAlerts}
          subtitle="Last 24 hours"
          icon={<Bell className="h-5 w-5 text-amber-400" />}
          color="bg-amber-500/10"
          loading={alertsLoading}
          headingLevel="h3"
        />
        <KPICard
          title="Market Regime"
          value="Normal"
          subtitle="Assessed by regime agent"
          icon={<TrendingUp className="h-5 w-5 text-emerald-400" />}
          color="bg-emerald-500/10"
          loading={false}
          headingLevel="h3"
        />
        <KPICard
          title="Agent Status"
          value={agents?.length ?? 0}
          subtitle={agentStatusText}
          icon={<Activity className="h-5 w-5 text-purple-400" />}
          color="bg-purple-500/10"
          loading={agentsLoading}
          headingLevel="h3"
        />
      </div>
    </section>
  );
}
```