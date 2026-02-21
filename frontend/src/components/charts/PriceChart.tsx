'use client';

import { useEffect, useRef } from 'react';
import { createChart, AreaSeries, ColorType, type IChartApi, type Time, type UTCTimestamp } from 'lightweight-charts';

interface PriceDataPoint {
  time: string | number;
  value: number;
}

interface PriceChartProps {
  data: PriceDataPoint[];
  title?: string;
  height?: number;
  color?: string;
}

export default function PriceChart({
  data,
  title,
  height = 300,
  color = '#3b82f6',
}: PriceChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  const usesTimestamps = data.length > 0 && typeof data[0].time === 'number';
  const browserTimezone = usesTimestamps
    ? Intl.DateTimeFormat().resolvedOptions().timeZone
    : null;

  useEffect(() => {
    if (!containerRef.current) return;

    const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const hasTimestamps = data.length > 0 && typeof data[0].time === 'number';

    const safeColor = /^#[0-9a-fA-F]{3,8}$/.test(color) ? color : '#3b82f6';

    const chart = createChart(containerRef.current, {
      height,
      layout: {
        background: { type: ColorType.Solid, color: 'transparent' },
        textColor: '#94a3b8',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        fontSize: 11,
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      crosshair: {
        vertLine: { color: '#475569', width: 1, style: 2, labelBackgroundColor: '#334155' },
        horzLine: { color: '#475569', width: 1, style: 2, labelBackgroundColor: '#334155' },
      },
      rightPriceScale: {
        borderColor: '#334155',
      },
      timeScale: {
        borderColor: '#334155',
        timeVisible: true,
      },
      localization: {
        timeFormatter: (time: Time) => {
          if (typeof time === 'number') {
            return new Intl.DateTimeFormat(undefined, {
              timeZone: tz,
              year: 'numeric',
              month: 'short',
              day: 'numeric',
            }).format(new Date((time as number) * 1000));
          }
          return String(time);
        },
      },
    });

    chartRef.current = chart;

    const areaSeries = chart.addSeries(AreaSeries, {
      lineColor: safeColor,
      topColor: `${safeColor}33`,
      bottomColor: `${safeColor}05`,
      lineWidth: 2,
    });

    if (data.length > 0) {
      const chartData = data
        .filter((d) => typeof d.value === 'number' && Number.isFinite(d.value))
        .map((d) => ({
          time: (hasTimestamps ? d.time as UTCTimestamp : d.time as Time),
          value: d.value,
        }));
      areaSeries.setData(chartData);
    }

    chart.timeScale().fitContent();

    const resizeObserver = new ResizeObserver(() => {
      if (containerRef.current) {
        chart.applyOptions({ width: containerRef.current.clientWidth });
      }
    });

    resizeObserver.observe(containerRef.current);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [data, height, color]);

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/50 p-4">
      {title && (
        <h3 className="mb-3 text-sm font-semibold text-white">{title}</h3>
      )}
      <div ref={containerRef} className="w-full" />
      {usesTimestamps && browserTimezone && (
        <p className="mt-2 text-right text-[10px] text-slate-500">
          All times in {browserTimezone}
        </p>
      )}
      {data.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <p className="text-sm text-slate-500">No chart data available</p>
        </div>
      )}
    </div>
  );
}
