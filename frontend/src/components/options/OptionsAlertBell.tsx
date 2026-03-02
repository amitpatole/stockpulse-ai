/**
 * TickerPulse AI - Options Alert Bell Component
 * Displays notification badge with unread alert count and dropdown.
 */

import React, { useState, useRef, useEffect } from 'react';
import { useOptionsAlerts } from '@/hooks/useOptionsAlerts';

export function OptionsAlertBell() {
  const { alerts, unreadCount, dismissAlert } = useOptionsAlerts({
    pollIntervalMs: 5000,
    limit: 10,
  });

  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'border-red-800 bg-red-950/50 text-red-200';
      case 'medium':
        return 'border-orange-800 bg-orange-950/50 text-orange-200';
      case 'low':
        return 'border-yellow-800 bg-yellow-950/50 text-yellow-200';
      default:
        return 'border-slate-700 bg-slate-900/50 text-slate-200';
    }
  };

  const getSeverityBadgeColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'bg-red-500/20 text-red-400';
      case 'medium':
        return 'bg-orange-500/20 text-orange-400';
      case 'low':
        return 'bg-yellow-500/20 text-yellow-400';
      default:
        return 'bg-slate-500/20 text-slate-400';
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-slate-300 hover:text-white transition-colors"
        title="Options Alerts"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
          />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute top-0 right-0 inline-flex items-center justify-center px-2 py-0.5 text-xs font-bold leading-none text-white bg-red-600 rounded-full">
            {unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 rounded-lg border border-slate-700 bg-slate-900 shadow-xl z-50">
          <div className="p-4 border-b border-slate-700">
            <h3 className="font-semibold text-slate-200">Options Alerts</h3>
            {unreadCount > 0 && (
              <p className="text-xs text-slate-400 mt-1">
                {unreadCount} unread alert{unreadCount > 1 ? 's' : ''}
              </p>
            )}
          </div>

          <div className="max-h-96 overflow-y-auto">
            {alerts.length === 0 ? (
              <div className="p-4 text-center text-slate-400 text-sm">
                No alerts
              </div>
            ) : (
              <div className="divide-y divide-slate-700">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className={`p-3 border-l-4 space-y-2 ${getSeverityColor(alert.severity)} ${
                      alert.dismissed ? 'opacity-60' : ''
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-sm">{alert.ticker}</span>
                          <span
                            className={`px-2 py-0.5 rounded text-xs font-medium ${getSeverityBadgeColor(
                              alert.severity
                            )}`}
                          >
                            {alert.severity}
                          </span>
                        </div>
                        <p className="text-xs mt-1">{alert.message}</p>
                        <p className="text-xs opacity-75 mt-1">
                          {new Date(alert.created_at).toLocaleString()}
                        </p>
                      </div>
                      {alert.dismissed === 0 && (
                        <button
                          onClick={() => dismissAlert(alert.id)}
                          className="px-2 py-1 text-xs bg-slate-700 hover:bg-slate-600 rounded transition-colors flex-shrink-0"
                          title="Dismiss alert"
                        >
                          ✓
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}