'use client';

import { clsx } from 'clsx';
import type { TimezoneMode } from '@/lib/types';

interface TimezoneToggleProps {
  mode: TimezoneMode;
  onModeChange: (mode: TimezoneMode) => void;
}

export default function TimezoneToggle({ mode, onModeChange }: TimezoneToggleProps) {
  return (
    <div
      role="group"
      aria-label="Timezone display"
      className="inline-flex rounded-lg border border-slate-700 bg-slate-900 p-0.5"
    >
      <button
        onClick={() => onModeChange('local')}
        aria-pressed={mode === 'local'}
        className={clsx(
          'rounded-md px-3 py-1 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/50',
          mode === 'local'
            ? 'bg-blue-600 text-white'
            : 'text-slate-400 hover:bg-slate-800 hover:text-white'
        )}
      >
        Local
      </button>
      <button
        onClick={() => onModeChange('ET')}
        aria-pressed={mode === 'ET'}
        className={clsx(
          'rounded-md px-3 py-1 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500/50',
          mode === 'ET'
            ? 'bg-blue-600 text-white'
            : 'text-slate-400 hover:bg-slate-800 hover:text-white'
        )}
      >
        ET (Market)
      </button>
    </div>
  );
}
