'use client';

import React, { useMemo } from 'react';

interface HistoryData {
  timestamp: string;
  usage_pct: number;
  call_count: number;
  errors: number;
}

interface UsageTimeSeriesProps {
  provider: string;
  data: HistoryData[];
  hours: number;
  interval: 'hourly' | 'daily';
}

export function UsageTimeSeries({
  provider,
  data,
  hours,
  interval
}: UsageTimeSeriesProps) {
  const chartData = useMemo(() => {
    if (!data || data.length === 0) {
      return null;
    }

    // Get dimensions
    const width = 800;
    const height = 300;
    const padding = { top: 20, right: 20, bottom: 40, left: 60 };
    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Find max usage for scaling
    const maxUsage = Math.max(...data.map(d => d.usage_pct), 100);
    const yScale = chartHeight / maxUsage;
    const xScale = chartWidth / Math.max(data.length - 1, 1);

    // Generate path points
    const points = data.map((d, i) => ({
      x: padding.left + i * xScale,
      y: padding.top + chartHeight - d.usage_pct * yScale,
      data: d
    }));

    // Build SVG path
    const pathData = points
      .map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`)
      .join(' ');

    return { width, height, padding, chartWidth, chartHeight, points, pathData, maxUsage };
  }, [data]);

  if (!chartData) {
    return <p className="text-gray-500">No data available</p>;
  }

  const { width, height, padding, chartWidth, chartHeight, points, pathData, maxUsage } = chartData;

  return (
    <div className="overflow-x-auto">
      <svg width={width} height={height} className="mx-auto">
        {/* Background zones */}
        {/* Healthy zone (0-80%) */}
        <rect
          x={padding.left}
          y={padding.top}
          width={chartWidth}
          height={(chartHeight * 80) / maxUsage}
          fill="#dcfce7"
          opacity="0.3"
        />
        {/* Warning zone (80-95%) */}
        <rect
          x={padding.left}
          y={padding.top + (chartHeight * 80) / maxUsage}
          width={chartWidth}
          height={(chartHeight * 15) / maxUsage}
          fill="#fef3c7"
          opacity="0.3"
        />
        {/* Critical zone (95%+) */}
        <rect
          x={padding.left}
          y={padding.top + (chartHeight * 95) / maxUsage}
          width={chartWidth}
          height={(chartHeight * 5) / maxUsage}
          fill="#fee2e2"
          opacity="0.3"
        />

        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map((value) => {
          const y = padding.top + chartHeight - (value / maxUsage) * chartHeight;
          return (
            <g key={`gridline-${value}`}>
              <line
                x1={padding.left}
                x2={padding.left + chartWidth}
                y1={y}
                y2={y}
                stroke="#e5e7eb"
                strokeWidth="1"
                strokeDasharray="4"
              />
              <text
                x={padding.left - 10}
                y={y + 4}
                textAnchor="end"
                fontSize="12"
                fill="#6b7280"
              >
                {value}%
              </text>
            </g>
          );
        })}

        {/* X-axis labels */}
        {points.map((p, i) => {
          // Show every Nth label to avoid crowding
          const showLabel = data.length <= 12 || i % Math.ceil(data.length / 6) === 0;
          if (!showLabel) return null;

          const timestamp = new Date(p.data.timestamp);
          const label = interval === 'hourly'
            ? timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
            : timestamp.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

          return (
            <text
              key={`label-${i}`}
              x={p.x}
              y={padding.top + chartHeight + 20}
              textAnchor="middle"
              fontSize="12"
              fill="#6b7280"
            >
              {label}
            </text>
          );
        })}

        {/* Axes */}
        <line
          x1={padding.left}
          x2={padding.left}
          y1={padding.top}
          y2={padding.top + chartHeight}
          stroke="#1f2937"
          strokeWidth="2"
        />
        <line
          x1={padding.left}
          x2={padding.left + chartWidth}
          y1={padding.top + chartHeight}
          y2={padding.top + chartHeight}
          stroke="#1f2937"
          strokeWidth="2"
        />

        {/* Data line */}
        <path
          d={pathData}
          fill="none"
          stroke="#3b82f6"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Data points */}
        {points.map((p, i) => (
          <circle
            key={`point-${i}`}
            cx={p.x}
            cy={p.y}
            r="3"
            fill="#3b82f6"
          />
        ))}

        {/* Tooltip hint */}
        {points.map((p, i) => (
          <g key={`tooltip-${i}`}>
            <rect
              x={p.x - 30}
              y={p.y - 45}
              width="60"
              height="35"
              fill="#1f2937"
              rx="4"
              opacity="0"
              className="hover-tooltip"
            />
            <text
              x={p.x}
              y={p.y - 20}
              textAnchor="middle"
              fontSize="11"
              fill="white"
              opacity="0"
              className="hover-tooltip-text"
            >
              {p.data.usage_pct.toFixed(1)}%
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}