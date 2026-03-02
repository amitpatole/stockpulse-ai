```typescript
export interface TourStep {
  id: string;
  title: string;
  description: string;
  selector?: string; // CSS selector for spotlight
  position: 'top' | 'bottom' | 'left' | 'right' | 'center';
}

export const TOUR_STEPS: TourStep[] = [
  {
    id: 'dashboard-kpis',
    title: 'Welcome to TickerPulse!',
    description: 'Monitor market metrics at a glance. KPI cards show key indicators and portfolio overview.',
    selector: '[data-tour="dashboard-kpis"]',
    position: 'bottom',
  },
  {
    id: 'watchlist',
    title: 'Your Stock Watchlist',
    description: 'Track favorite stocks in real-time. Add stocks and see live price updates.',
    selector: '[data-tour="watchlist"]',
    position: 'right',
  },
  {
    id: 'news-feed',
    title: 'Latest Market News',
    description: 'Stay updated with latest market news and analysis. Filter by ticker.',
    selector: '[data-tour="news-feed"]',
    position: 'left',
  },
  {
    id: 'sidebar-agents',
    title: 'AI Agents',
    description: 'AI agents run automated analysis. Create and configure agents here.',
    selector: '[data-tour="sidebar-agents"]',
    position: 'right',
  },
  {
    id: 'sidebar-research',
    title: 'Research Reports',
    description: 'Deep dive into research reports and analysis. Generate custom research on demand.',
    selector: '[data-tour="sidebar-research"]',
    position: 'right',
  },
  {
    id: 'sidebar-scheduler',
    title: 'Task Scheduler',
    description: 'Schedule recurring analysis tasks. Automate your workflow.',
    selector: '[data-tour="sidebar-scheduler"]',
    position: 'right',
  },
  {
    id: 'sidebar-settings',
    title: 'Settings & Configuration',
    description: 'Configure AI providers, API keys, and preferences. Customize your experience.',
    selector: '[data-tour="sidebar-settings"]',
    position: 'right',
  },
  {
    id: 'complete',
    title: 'Tour Complete! ✓',
    description: 'You\'re all set! You now know the basics. Restart anytime from Settings.',
    position: 'center',
  },
];
```