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
      className="flex items-center rounded-lg bg-slate-800 p-0.5"
      role="group"
      aria-label="Timezone display mode"
    >
      <button
        onClick={() => onModeChange('local')}
        aria-pressed={mode === 'local'}
        className={clsx(
          'rounded-md px-3 py-1 text-xs font-medium transition-colors',
          mode === 'local'
            ? 'bg-slate-600 text-white'
            : 'text-slate-400 hover:text-slate-200'
        )}
      >
        Local
      </button>
      <button
        onClick={() => onModeChange('ET')}
        aria-pressed={mode === 'ET'}
        className={clsx(
          'rounded-md px-3 py-1 text-xs font-medium transition-colors',
          mode === 'ET'
            ? 'bg-slate-600 text-white'
            : 'text-slate-400 hover:text-slate-200'
        )}
      >
        ET (Market)
      </button>
    </div>
  );
}
