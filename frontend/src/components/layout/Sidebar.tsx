'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Bot,
  FileSearch,
  Calendar,
  Settings,
  ChevronLeft,
  ChevronRight,
  Activity,
  Zap,
} from 'lucide-react';
import { clsx } from 'clsx';

const NAV_ITEMS = [
  { href: '/', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/agents', label: 'Agents', icon: Bot },
  { href: '/research', label: 'Research', icon: FileSearch },
  { href: '/scheduler', label: 'Scheduler', icon: Calendar },
  { href: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <>
      {/* Skip to main content link */}
      <a
        href="#main"
        className="sr-only focus:not-sr-only fixed top-0 left-0 z-50 bg-blue-600 text-white px-4 py-2 rounded-b focus-visible:outline-none"
      >
        Skip to main content
      </a>

      {/* Navigation landmark */}
      <nav
        className={clsx(
          'fixed left-0 top-0 z-40 flex h-screen flex-col border-r border-slate-700/50 bg-slate-900 transition-all duration-300',
          collapsed ? 'w-16' : 'w-60'
        )}
        aria-label="Main navigation"
        role="navigation"
      >
        {/* Logo section */}
        <div className="flex h-16 items-center gap-3 border-b border-slate-700/50 px-4">
          <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-blue-600">
            <Zap className="h-5 w-5 text-white" aria-hidden="true" />
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <h1 className="text-sm font-bold text-white tracking-wide">TickerPulse AI</h1>
              <p className="text-[10px] text-slate-400">v3.0</p>
            </div>
          )}
        </div>

        {/* Navigation links */}
        <nav className="flex-1 space-y-1 px-2 py-4" aria-label="Navigation menu">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900',
                  isActive
                    ? 'bg-blue-600/20 text-blue-400'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                )}
                title={collapsed ? item.label : undefined}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                {!collapsed && <span>{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* System status section */}
        <section className="border-t border-slate-700/50 p-3" aria-label="System status">
          <div
            className={clsx('flex items-center gap-2', collapsed && 'justify-center')}
            role="status"
            aria-live="polite"
          >
            <Activity className="h-4 w-4 text-emerald-400" aria-hidden="true" />
            {!collapsed && <span className="text-xs text-slate-400">System Online</span>}
          </div>
        </section>

        {/* Collapse/Expand button */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-expanded={!collapsed}
          className="flex h-10 items-center justify-center border-t border-slate-700/50 text-slate-400 hover:bg-slate-800 hover:text-white transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" aria-hidden="true" />
          ) : (
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
          )}
        </button>
      </nav>

      {/* Spacer for main content */}
      <div className={clsx('flex-shrink-0 transition-all duration-300', collapsed ? 'w-16' : 'w-60')} />
    </>
  );
}