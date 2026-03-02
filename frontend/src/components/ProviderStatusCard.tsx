'use client';

import React, { useState, useEffect } from 'react';

interface ProviderStatusCardProps {
  provider: string;
  limit_value: number;
  current_usage: number;
  usage_pct: number;
  reset_in_seconds: number;
  status: 'healthy' | 'warning' | 'critical' | 'error';
  onClick?: () => void;
}

export function ProviderStatusCard({
  provider,
  limit_value,
  current_usage,
  usage_pct,
  reset_in_seconds,
  status,
  onClick
}: ProviderStatusCardProps) {
  const [countdown, setCountdown] = useState(reset_in_seconds);

  // Update countdown every second
  useEffect(() => {
    setCountdown(reset_in_seconds);
    const interval = setInterval(() => {
      setCountdown(prev => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [reset_in_seconds]);

  const formatCountdown = (seconds: number) => {
    if (seconds === 0) return 'Resetting now';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m ${secs}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'healthy':
        return '✓';
      case 'warning':
        return '⚠';
      case 'critical':
        return '✕';
      default:
        return '?';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return 'bg-green-50 border-green-200';
      case 'warning':
        return 'bg-amber-50 border-amber-200';
      case 'critical':
        return 'bg-red-50 border-red-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  const getUsageBarColor = () => {
    if (usage_pct >= 95) return 'bg-red-500';
    if (usage_pct >= 80) return 'bg-amber-500';
    return 'bg-green-500';
  };

  return (
    <div
      onClick={onClick}
      className={`
        rounded-lg border-2 p-6 cursor-pointer transition
        hover:shadow-lg ${getStatusColor()}
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-900">{provider}</h3>
        <span className={`
          text-2xl font-bold
          ${status === 'healthy' && 'text-green-600'}
          ${status === 'warning' && 'text-amber-600'}
          ${status === 'critical' && 'text-red-600'}
          ${status === 'error' && 'text-gray-600'}
        `}>
          {getStatusIcon()}
        </span>
      </div>

      {/* Usage info */}
      <div className="mb-3">
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm text-slate-600">
            {current_usage} / {limit_value} calls
          </span>
          <span className="text-sm font-semibold text-slate-900">
            {usage_pct.toFixed(1)}%
          </span>
        </div>

        {/* Usage bar */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${getUsageBarColor()}`}
            style={{ width: `${Math.min(usage_pct, 100)}%` }}
          />
        </div>
      </div>

      {/* Reset countdown */}
      <div className="text-xs text-slate-600">
        Resets in: <span className="font-semibold">{formatCountdown(countdown)}</span>
      </div>

      {/* Status badge */}
      <div className="mt-3">
        <span className={`
          px-2 py-1 rounded text-xs font-semibold uppercase
          ${status === 'healthy' && 'bg-green-100 text-green-800'}
          ${status === 'warning' && 'bg-amber-100 text-amber-800'}
          ${status === 'critical' && 'bg-red-100 text-red-800'}
          ${status === 'error' && 'bg-gray-100 text-gray-800'}
        `}>
          {status}
        </span>
      </div>
    </div>
  );
}