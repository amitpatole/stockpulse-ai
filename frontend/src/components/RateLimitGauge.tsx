'use client';

import React from 'react';

interface RateLimitGaugeProps {
  provider: string;
  usage_pct: number;
  limit_value: number;
  current_usage: number;
  status: 'healthy' | 'warning' | 'critical' | 'error';
}

export function RateLimitGauge({
  provider,
  usage_pct,
  limit_value,
  current_usage,
  status
}: RateLimitGaugeProps) {
  // Determine color based on status
  const getColor = () => {
    switch (status) {
      case 'healthy':
        return '#10b981'; // green
      case 'warning':
        return '#f59e0b'; // amber
      case 'critical':
        return '#ef4444'; // red
      default:
        return '#6b7280'; // gray
    }
  };

  const getBackgroundColor = () => {
    switch (status) {
      case 'healthy':
        return '#dcfce7'; // light green
      case 'warning':
        return '#fef3c7'; // light amber
      case 'critical':
        return '#fee2e2'; // light red
      default:
        return '#f3f4f6'; // light gray
    }
  };

  const color = getColor();
  const bgColor = getBackgroundColor();
  const circumference = 2 * Math.PI * 45; // radius = 45
  const strokeDashoffset = circumference - (usage_pct / 100) * circumference;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 flex flex-col items-center justify-center">
      <h3 className="text-lg font-semibold text-slate-900 mb-4">{provider}</h3>
      
      {/* Circular Gauge */}
      <div className="relative w-32 h-32 flex items-center justify-center mb-4">
        <svg width="140" height="140" className="transform -rotate-90">
          <circle
            cx="70"
            cy="70"
            r="45"
            fill="none"
            stroke={bgColor}
            strokeWidth="8"
          />
          <circle
            cx="70"
            cy="70"
            r="45"
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 0.3s ease' }}
          />
        </svg>
        <div className="absolute text-center">
          <div className="text-2xl font-bold text-slate-900">{Math.round(usage_pct)}%</div>
          <div className="text-xs text-slate-600">{current_usage}/{limit_value}</div>
        </div>
      </div>

      {/* Status Label */}
      <span className={`
        px-3 py-1 rounded-full text-xs font-semibold uppercase
        ${status === 'healthy' && 'bg-green-100 text-green-800'}
        ${status === 'warning' && 'bg-amber-100 text-amber-800'}
        ${status === 'critical' && 'bg-red-100 text-red-800'}
        ${status === 'error' && 'bg-gray-100 text-gray-800'}
      `}>
        {status}
      </span>
    </div>
  );
}