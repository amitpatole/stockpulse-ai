```typescript
'use client';

import { Bell, Wifi, WifiOff, Search } from 'lucide-react';
import { clsx } from 'clsx';
import { useSSE } from '@/hooks/useSSE';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export default function Header({ title, subtitle }: HeaderProps) {
  const { connected, recentAlerts } = useSSE();
  const unreadAlerts = recentAlerts.length;

  return (
    <header className="flex h-16 items-center justify-between border-b border-slate-700/50 bg-slate-900/50 px-6 backdrop-blur-sm" role="banner">
      <div>
        <h1 className="text-lg font-semibold text-white">{title}</h1>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {/* Search section with proper label association */}
        <div className="hidden items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/50 px-3 py-1.5 md:flex">
          <label htmlFor="header-search" className="sr-only">
            Search
          </label>
          <Search className="h-4 w-4 text-slate-500" aria-hidden="true" />
          <input
            id="header-search"
            type="text"
            placeholder="Search..."
            aria-label="Search alerts and stocks"
            className="bg-transparent text-xs text-slate-500 placeholder-slate-500 outline-none focus:ring-0 focus-visible:outline-none"
          />
          <kbd className="ml-4 rounded bg-slate-700 px-1.5 py-0.5 text-[10px] text-slate-400" aria-hidden="true">
            /
          </kbd>
        </div>

        {/* Alerts button with dynamic label */}
        <button
          aria-label={`View alerts${unreadAlerts > 0 ? ` (${unreadAlerts} unread)` : ''}`}
          className="relative rounded-lg p-2 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
        >
          <Bell className="h-5 w-5" aria-hidden="true" />
          {unreadAlerts > 0 && (
            <span
              className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white"
              aria-label={`${unreadAlerts} unread alerts`}
            >
              {unreadAlerts > 9 ? '9+' : unreadAlerts}
            </span>
          )}
        </button>

        {/* Connection status indicator */}
        <div
          className={clsx(
            'flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium',
            connected ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
          )}
          role="status"
          aria-live="polite"
          aria-label={`Connection status: ${connected ? 'Live' : 'Offline'}`}
        >
          {connected ? (
            <Wifi className="h-3 w-3" aria-hidden="true" />
          ) : (
            <WifiOff className="h-3 w-3" aria-hidden="true" />
          )}
          <span>{connected ? 'Live' : 'Offline'}</span>
        </div>
      </div>
    </header>
  );
}
```