```typescript
// ============================================================
// TickerPulse AI v3.0 - API Client
// ============================================================

import type {
  Stock,
  StockSearchResult,
  AIRating,
  Agent,
  AgentRun,
  ScheduledJob,
  NewsArticle,
  Alert,
  CostSummary,
  AIProvider,
  HealthCheck,
  ResearchBrief,
} from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

interface PaginationMeta {
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
  has_previous: boolean;
}

interface PaginatedResponse<T> {
  data: T[];
  meta: PaginationMeta;
}

async function request<T>(path: string, options?: RequestInit & { signal?: AbortSignal }): Promise<T> {
  const url = `${API_BASE}${path}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!res.ok) {
      const body = await res.text();
      let message = `API error: ${res.status}`;
      try {
        const json = JSON.parse(body);
        message = json.error || json.message || message;
      } catch {
        if (body) message = body;
      }
      throw new ApiError(message, res.status);
    }

    const text = await res.text();
    if (!text) return {} as T;
    return JSON.parse(text) as T;
  } catch (err) {
    // Handle AbortError gracefully - request was cancelled by user/unmount
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw err;
    }
    if (err instanceof ApiError) throw err;
    throw new ApiError(
      `Failed to connect to API: ${err instanceof Error ? err.message : 'Unknown error'}`,
      0
    );
  }
}

// ---- Stocks ----

export async function getStocks(limit: number = 50, offset: number = 0): Promise<Stock[]> {
  const params = new URLSearchParams();
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  
  const data = await request<PaginatedResponse<Stock> | Stock[]>(
    `/api/stocks?${params.toString()}`
  );
  
  // Handle both old array format and new paginated format
  if (Array.isArray(data)) return data;
  if ('data' in data) return data.data;
  return [];
}

export async function searchStocks(query: string): Promise<StockSearchResult[]> {
  if (!query.trim()) return [];
  return request<StockSearchResult[]>(`/api/stocks/search?q=${encodeURIComponent(query.trim())}`);
}

export async function addStock(ticker: string, name?: string): Promise<Stock> {
  const body: Record<string, string> = { ticker: ticker.toUpperCase() };
  if (name) body.name = name;
  return request<Stock>('/api/stocks', {
    method: 'POST',
    body: JSON.stringify(body),
  });
}

export async function deleteStock(ticker: string): Promise<void> {
  await request<void>(`/api/stocks/${ticker.toUpperCase()}`, {
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

export async function saveAIProvider(provider: string, apiKey: string, model?: string): Promise<{ success: boolean }> {
  return request<{ success: boolean }>('/api/settings/ai-provider', {
    method: 'POST',
    body: JSON.stringify({
      provider,
      api_key: apiKey,
      model: model || undefined,
    }),
  });
}

export async function setAgentFramework(framework: string): Promise<{ success: boolean; framework: string }> {
  return request<{ success: boolean; framework: string }>('/api/settings/agent-framework', {
    method: 'POST',
    body: JSON.stringify({ framework }),
  });
}

export async function saveBudgetSettings(monthlyBudget: number, dailyWarning: number): Promise<{ success: boolean }> {
  return request<{ success: boolean }>('/api/settings/budget', {
    method: 'POST',
    body: JSON.stringify({
      monthly_budget: monthlyBudget,
      daily_warning: dailyWarning,
    }),
  });
}

export async function getBudgetSettings(): Promise<{ monthly_budget: number; daily_warning: number }> {
  return request<{ monthly_budget: number; daily_warning: number }>('/api/settings/budget');
}

// ---- Health ----

export async function getHealth(): Promise<HealthCheck> {
  return request<HealthCheck>('/api/health');
}

// ---- Research ----

export async function getResearchBriefs(ticker?: string, limit: number = 50, offset: number = 0): Promise<ResearchBrief[]> {
  const params = new URLSearchParams();
  if (ticker) params.set('ticker', ticker);
  params.set('limit', String(limit));
  params.set('offset', String(offset));
  
  const data = await request<PaginatedResponse<ResearchBrief> | ResearchBrief[]>(
    `/api/research/briefs?${params.toString()}`
  );
  
  // Handle both old array format and new paginated format
  if (Array.isArray(data)) return data;
  if ('data' in data) return data.data;
  return [];
}

export async function generateResearchBrief(ticker?: string): Promise<ResearchBrief> {
  return request<ResearchBrief>('/api/research/briefs', {
    method: 'POST',
    body: JSON.stringify(ticker ? { ticker } : {}),
  });
}

export { ApiError, type PaginationMeta, type PaginatedResponse };
```