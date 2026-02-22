'use client';

import { clsx } from 'clsx';
import type { TimezoneMode } from '@/lib/types';

interface TimezoneToggleProps {
  mode: TimezoneMode;
  onModeChange: (mode: TimezoneMode) => void;
}

const OPTIONS: { value: TimezoneMode; label: string }[] = [
  { value: 'local', label: 'Local' },
  { value: 'ET', label: 'ET (Market)' },
];

export default function TimezoneToggle({ mode, onModeChange }: TimezoneToggleProps) {
  return (
    <div
      role="group"
      aria-label="Timezone display mode"
      className="flex rounded-lg border border-slate-700 bg-slate-900 p-0.5"
    >
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          onClick={() => onModeChange(opt.value)}
          aria-pressed={mode === opt.value}
          className={clsx(
            'rounded-md px-3 py-1.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/50',
            mode === opt.value
              ? 'bg-blue-600 text-white'
              : 'text-slate-400 hover:bg-slate-800 hover:text-white'
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
