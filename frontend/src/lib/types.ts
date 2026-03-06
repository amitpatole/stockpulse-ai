// =====================================================
export interface PriceAlert {
  id: number;
  ticker: string;
  alert_type: 'above' | 'below' | 'change_percent_up' | 'change_percent_down';
  threshold: number;
  is_active: boolean;
  triggered_count: number;
  last_triggered_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PriceAlertTriggerEvent {
  alert_id: number;
  ticker: string;
  alert_type: string;
  threshold: number;
  current_price: number;
  timestamp: string;
}

export interface PaginationMeta {
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
  has_previous: boolean;
}

export interface PriceAlertsListResponse {
  alerts: PriceAlert[];
  meta: PaginationMeta;
}

export interface ScheduledJob {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  next_run: string | null;
  last_run?: string | null;
  trigger: string;
  status?: string;
}

export interface NewsArticle {
  id: number;
  ticker: string;
  title: string;
  source: string;
  sentiment_label: string;
  sentiment_score: number;
  created_at: string;
  url: string;
  summary?: string;
}

export interface Alert {
  id: number;
  ticker: string;
  type: string;
  message: string;
  severity: string;
  created_at: string;
  read?: boolean;
}

export interface CostSummary {
  total_cost?: number;
  total_cost_usd?: number;
  daily_costs?: DailyCost[];
  by_agent?: Record<string, number | { cost_usd: number; display_name: string; runs: number; tokens_used: number }>;
  period_days?: number;
  range_label?: string;
  total_runs?: number;
  total_tokens?: number;
}

export interface DailyCost {
  date: string;
  cost: number;
  runs: number;
}

export interface AIProvider {
  name: string;
  display_name: string;
  configured: boolean;
  models: string[];
  default_model?: string;
  status?: string;
}

export interface HealthCheck {
  status: string;
  version?: string;
  uptime?: number;
  database?: string;
  agents?: Record<string, string>;
}

export interface ResearchBriefMetrics {
  ticker?: string;
  extracted_at?: string;
  rsi?: number;
  macd_signal?: string;
  sentiment_score?: number;
  price_change_pct?: number;
  support_level?: number;
  resistance_level?: number;
}

export interface ResearchBrief {
  id: number;
  ticker: string;
  title: string;
  content: string;
  agent_name: string;
  created_at: string;
  model_used?: string;
  executive_summary?: string;
  key_metrics?: ResearchBriefMetrics;
}

// SSE Event Types
export type SSEEventType = 'agent_status' | 'alert' | 'job_complete' | 'heartbeat' | 'news' | 'rating_update';

export interface SSEEvent {
  type: SSEEventType;
  data: Record<string, unknown>;
  timestamp?: string;
}

export interface AgentStatusEvent {
  agent_name: string;
  status: string;
  message?: string;
}

export interface AlertEvent {
  ticker: string;
  type: string;
  message: string;
  severity: string;
}

export interface JobCompleteEvent {
  job_id: string;
  job_name: string;
  status: string;
  duration_ms?: number;
}

// Rating color mapping
export const RATING_COLORS: Record<string, string> = {
  STRONG_BUY: '#10b981',
  BUY: '#22c55e',
  HOLD: '#f59e0b',
  SELL: '#ef4444',
  STRONG_SELL: '#dc2626',
};

export const RATING_BG_CLASSES: Record<string, string> = {
  STRONG_BUY: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  BUY: 'bg-green-500/20 text-green-400 border-green-500/30',
  HOLD: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  SELL: 'bg-red-500/20 text-red-400 border-red-500/30',
  STRONG_SELL: 'bg-red-700/20 text-red-500 border-red-700/30',
};

export const SENTIMENT_COLORS: Record<string, string> = {
  positive: 'bg-emerald-500/20 text-emerald-400',
  neutral: 'bg-slate-500/20 text-slate-400',
  negative: 'bg-red-500/20 text-red-400',
  mixed: 'bg-amber-500/20 text-amber-400',
};

export const AGENT_STATUS_COLORS: Record<string, string> = {
  idle: 'bg-emerald-500',
  running: 'bg-blue-500',
  error: 'bg-red-500',
  disabled: 'bg-slate-500',
};
