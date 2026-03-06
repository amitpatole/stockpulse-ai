// =====================================================
import { PriceAlert, PriceAlertsListResponse } from './types';

// Price Alerts API
export async function getPriceAlerts(
  limit = 20,
  offset = 0,
  ticker?: string,
  activeOnly = false,
): Promise<PriceAlertsListResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });
  if (ticker) params.append('ticker', ticker);
  if (activeOnly) params.append('active_only', 'true');

  return request(`/price-alerts?${params.toString()}`);
}

export async function getPriceAlert(id: number): Promise<PriceAlert> {
  return request(`/price-alerts/${id}`);
}

export async function createPriceAlert(
  ticker: string,
  alertType: string,
  threshold: number,
): Promise<PriceAlert> {
  return request('/price-alerts', {
    method: 'POST',
    body: JSON.stringify({
      ticker,
      alert_type: alertType,
      threshold,
    }),
  });
}

export async function updatePriceAlert(
  id: number,
  threshold?: number,
  isActive?: boolean,
): Promise<PriceAlert> {
  return request(`/price-alerts/${id}`, {
    method: 'PUT',
    body: JSON.stringify({
      ...(threshold !== undefined && { threshold }),
      ...(isActive !== undefined && { is_active: isActive }),
    }),
  });
}

export async function deletePriceAlert(id: number): Promise<void> {
  await request(`/price-alerts/${id}`, {
    method: 'DELETE',
  });
}

// ---- News ----

export async function getNews(ticker?: string, limit = 50): Promise<NewsArticle[]> {
  const params = new URLSearchParams();
  if (ticker) params.set('ticker', ticker);
  params.set('limit', String(limit));
  const data = await request<{ articles: NewsArticle[] } | NewsArticle[]>(
    `/api/news?${params.toString()}`
  );
  if (Array.isArray(data)) return data;
  return data.articles || [];
}

// ---- Alerts ----

export async function getAlerts(): Promise<Alert[]> {
  const data = await request<{ alerts: Alert[] } | Alert[]>('/api/alerts');
  if (Array.isArray(data)) return data;
  return data.alerts || [];
}

// ---- AI Ratings ----

export async function getRatings(): Promise<AIRating[]> {
  const data = await request<{ ratings: AIRating[] } | AIRating[]>('/api/ai/ratings');
  if (Array.isArray(data)) return data;
  return data.ratings || [];
}

export async function getRating(ticker: string): Promise<AIRating> {
  return request<AIRating>(`/api/ai/rating/${ticker.toUpperCase()}`);
}

// ---- Agents ----

export async function getAgents(): Promise<Agent[]> {
  const data = await request<{ agents: Agent[] } | Agent[]>('/api/agents');
  if (Array.isArray(data)) return data;
  return data.agents || [];
}

export async function getAgent(name: string): Promise<Agent> {
  return request<Agent>(`/api/agents/${name}`);
}

export async function runAgent(name: string): Promise<{ message: string; run_id?: number }> {
  return request<{ message: string; run_id?: number }>(`/api/agents/${name}/run`, {
    method: 'POST',
  });
}

export async function getAgentRuns(limit = 50): Promise<AgentRun[]> {
  const data = await request<{ runs: AgentRun[] } | AgentRun[]>(
    `/api/agents/runs?limit=${limit}`
  );
  if (Array.isArray(data)) return data;
  return data.runs || [];
}

export async function getCostSummary(days = 30): Promise<CostSummary> {
  return request<CostSummary>(`/api/agents/costs?days=${days}`);
}

// ---- Scheduler ----

export async function getSchedulerJobs(): Promise<ScheduledJob[]> {
  const data = await request<{ jobs: ScheduledJob[] } | ScheduledJob[]>('/api/scheduler/jobs');
  if (Array.isArray(data)) return data;
  return data.jobs || [];
}

export async function triggerJob(id: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/api/scheduler/jobs/${id}/trigger`, {
    method: 'POST',
  });
}

export async function pauseJob(id: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/api/scheduler/jobs/${id}/pause`, {
    method: 'POST',
  });
}

export async function resumeJob(id: string): Promise<{ message: string }> {
  return request<{ message: string }>(`/api/scheduler/jobs/${id}/resume`, {
    method: 'POST',
  });
}

// ---- Settings ----

export async function getAIProviders(): Promise<AIProvider[]> {
  const data = await request<{ providers: AIProvider[] } | AIProvider[]>(
    '/api/settings/ai-providers'
  );
  if (Array.isArray(data)) return data;
  return data.providers || [];
}

// ---- Health ----

export async function getHealth(): Promise<HealthCheck> {
  return request<HealthCheck>('/api/health');
}

// ---- Chart Data ----

export interface ChartDataPoint {
  timestamp: number;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface ChartResponse {
  ticker: string;
  period: string;
  data: ChartDataPoint[];
  currency_symbol: string;
  stats: {
    current_price: number;
    open_price: number;
    high_price: number;
    low_price: number;
    price_change: number;
    price_change_percent: number;
    total_volume: number;
  };
}

export async function getChartData(ticker: string, period = '1mo'): Promise<ChartResponse> {
  return request<ChartResponse>(`/api/chart/${ticker.toUpperCase()}?period=${period}`);
}

// ---- Research ----

export async function getResearchBriefs(ticker?: string): Promise<ResearchBrief[]> {
  const params = new URLSearchParams();
  if (ticker) params.set('ticker', ticker);
  params.set('limit', '50');
  const data = await request<ResearchBrief[]>(
    `/api/research/briefs?${params.toString()}`
  );
  return Array.isArray(data) ? data : [];
}

export async function generateResearchBrief(ticker?: string): Promise<ResearchBrief> {
  return request<ResearchBrief>('/api/research/briefs', {
    method: 'POST',
    body: JSON.stringify(ticker ? { ticker } : {}),
  });
}

export async function exportBriefPDF(briefId: number, includeMetrics = true): Promise<void> {
  const url = `${API_BASE}/api/research/briefs/${briefId}/export`;
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ include_metrics: includeMetrics }),
    });

    if (!response.ok) {
      throw new ApiError(`Failed to export PDF: ${response.status}`, response.status);
    }

    const blob = await response.blob();
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `brief_${briefId}.pdf`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  } catch (err) {
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      `Failed to download PDF: ${err instanceof Error ? err.message : 'Unknown error'}`,
      0
    );
  }
}

export { ApiError };
