'use client';

import { useState, useCallback } from 'react';
import { Bell, Play, Trash2, ToggleLeft, ToggleRight, Loader2 } from 'lucide-react';
import { clsx } from 'clsx';
import { useApi } from '@/hooks/useApi';
import { listPriceAlerts, updateAlertSoundType } from '@/lib/api';
import type { PriceAlert } from '@/lib/types';

const SOUND_OPTIONS = [
  { value: 'default', label: 'Default' },
  { value: 'chime', label: 'Chime' },
  { value: 'alarm', label: 'Alarm' },
  { value: 'silent', label: 'Silent' },
] as const;

type SoundType = 'default' | 'chime' | 'alarm' | 'silent';

function formatCondition(conditionType: string, threshold: number): string {
  switch (conditionType) {
    case 'price_above':
      return `Price above $${threshold.toFixed(2)}`;
    case 'price_below':
      return `Price below $${threshold.toFixed(2)}`;
    case 'pct_change':
      return `±${threshold.toFixed(1)}% change`;
    default:
      return `${conditionType} ${threshold}`;
  }
}

function previewSound(soundType: SoundType, volume: number = 70): void {
  if (soundType === 'silent') return;
  const audio = new Audio(`/sounds/${soundType}.mp3`);
  audio.volume = volume / 100;
  audio.play().catch(() => {
    // Ignore autoplay policy errors
  });
}

function SkeletonRow() {
  return (
    <tr>
      {Array.from({ length: 6 }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <div className="h-4 animate-pulse rounded bg-slate-700/50" />
        </td>
      ))}
    </tr>
  );
}

interface AlertRowProps {
  alert: PriceAlert;
  onSoundChange: (id: number, sound: SoundType) => Promise<void>;
  onDelete: (id: number) => void;
  updating: boolean;
}

function AlertRow({ alert, onSoundChange, onDelete, updating }: AlertRowProps) {
  const [localSound, setLocalSound] = useState<SoundType>(alert.sound_type);
  const [rowError, setRowError] = useState<string | null>(null);

  const handleSoundChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newSound = e.target.value as SoundType;
    setLocalSound(newSound);
    setRowError(null);
    try {
      await onSoundChange(alert.id, newSound);
    } catch (err) {
      setRowError(err instanceof Error ? err.message : 'Update failed');
      setLocalSound(alert.sound_type); // revert on error
    }
  };

  const statusBadge = alert.triggered_at
    ? 'bg-amber-500/20 text-amber-400 border-amber-500/30'
    : alert.enabled
    ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
    : 'bg-slate-500/20 text-slate-400 border-slate-500/30';

  const statusLabel = alert.triggered_at ? 'Triggered' : alert.enabled ? 'Active' : 'Disabled';

  return (
    <tr className="border-b border-slate-700/30 hover:bg-slate-800/30 transition-colors">
      <td className="px-4 py-3">
        <span className="font-mono text-sm font-semibold text-white">{alert.ticker}</span>
      </td>
      <td className="px-4 py-3">
        <span className="text-sm text-slate-300">
          {formatCondition(alert.condition_type, alert.threshold)}
        </span>
      </td>
      <td className="px-4 py-3">
        <span
          className={clsx(
            'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium',
            statusBadge
          )}
        >
          {statusLabel}
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <select
            aria-label={`Sound for ${alert.ticker} alert`}
            value={localSound}
            onChange={handleSoundChange}
            disabled={updating}
            className="rounded-lg border border-slate-700 bg-slate-800/50 px-2 py-1.5 text-xs text-white outline-none focus:border-blue-500 disabled:opacity-50"
          >
            {SOUND_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value} className="bg-slate-800">
                {opt.label}
              </option>
            ))}
          </select>
          <button
            type="button"
            aria-label={`Preview ${localSound} sound for ${alert.ticker}`}
            onClick={() => previewSound(localSound)}
            disabled={localSound === 'silent'}
            className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-700 text-slate-300 transition-colors hover:bg-slate-600 hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
            title="Preview sound"
          >
            <Play className="h-3 w-3" />
          </button>
        </div>
        {rowError && (
          <p className="mt-1 text-xs text-red-400">{rowError}</p>
        )}
      </td>
      <td className="px-4 py-3 text-xs text-slate-500">
        {alert.created_at ? new Date(alert.created_at).toLocaleDateString() : '—'}
      </td>
      <td className="px-4 py-3">
        <button
          type="button"
          aria-label={`Delete alert for ${alert.ticker}`}
          onClick={() => onDelete(alert.id)}
          className="flex h-7 w-7 items-center justify-center rounded-lg text-slate-500 transition-colors hover:bg-red-500/20 hover:text-red-400"
          title="Delete alert"
        >
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </td>
    </tr>
  );
}

export default function PriceAlertsPanel() {
  const {
    data: alerts,
    loading,
    error,
    refetch,
  } = useApi<PriceAlert[]>(listPriceAlerts, []);

  const [updating, setUpdating] = useState<Record<number, boolean>>({});

  const handleSoundChange = useCallback(
    async (alertId: number, soundType: SoundType) => {
      setUpdating((prev) => ({ ...prev, [alertId]: true }));
      try {
        await updateAlertSoundType(alertId, soundType);
      } finally {
        setUpdating((prev) => ({ ...prev, [alertId]: false }));
      }
    },
    []
  );

  const handleDelete = useCallback(
    async (alertId: number) => {
      try {
        await fetch(`/api/alerts/${alertId}`, { method: 'DELETE' });
        refetch();
      } catch {
        // Silently refetch to sync state
        refetch();
      }
    },
    [refetch]
  );

  return (
    <div className="rounded-xl border border-slate-700/50 bg-slate-800/50">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-700/50 px-5 py-4">
        <div className="flex items-center gap-3">
          <Bell className="h-5 w-5 text-blue-400" />
          <div>
            <p className="text-sm font-medium text-white">Price Alerts</p>
            <p className="text-xs text-slate-400">
              Manage per-alert notification sounds
            </p>
          </div>
        </div>
        <button
          onClick={refetch}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg bg-slate-700 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-slate-600 disabled:opacity-50"
        >
          {loading ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
          Refresh
        </button>
      </div>

      {/* Error banner */}
      {error && (
        <div className="px-5 py-3">
          <p role="alert" className="text-sm text-red-400">
            Failed to load price alerts: {error}
          </p>
        </div>
      )}

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-slate-700/30">
              <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-500">
                Ticker
              </th>
              <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-500">
                Condition
              </th>
              <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-500">
                Status
              </th>
              <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-500">
                Sound
              </th>
              <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-500">
                Created
              </th>
              <th className="px-4 py-3 text-xs font-medium uppercase tracking-wider text-slate-500">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {loading && !alerts && (
              <>
                <SkeletonRow />
                <SkeletonRow />
                <SkeletonRow />
              </>
            )}

            {alerts && alerts.length === 0 && !loading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-sm text-slate-500">
                  No price alerts configured.
                </td>
              </tr>
            )}

            {alerts &&
              alerts.map((alert) => (
                <AlertRow
                  key={alert.id}
                  alert={alert}
                  onSoundChange={handleSoundChange}
                  onDelete={handleDelete}
                  updating={!!updating[alert.id]}
                />
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
