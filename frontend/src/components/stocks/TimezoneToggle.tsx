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
      className="flex items-center rounded-full border border-slate-700 bg-slate-800 p-0.5"
      role="group"
      aria-label="Timezone selection"
    >
      <button
        type="button"
        onClick={() => onModeChange('local')}
        className={clsx(
          'rounded-full px-3 py-1 text-xs font-medium transition-colors',
          mode === 'local'
            ? 'bg-slate-600 text-white'
            : 'text-slate-400 hover:text-slate-200'
        )}
        aria-pressed={mode === 'local'}
      >
        Local
      </button>
      <button
        type="button"
        onClick={() => onModeChange('ET')}
        className={clsx(
          'rounded-full px-3 py-1 text-xs font-medium transition-colors',
          mode === 'ET'
            ? 'bg-slate-600 text-white'
            : 'text-slate-400 hover:text-slate-200'
        )}
        aria-pressed={mode === 'ET'}
      >
        ET (Market)
      </button>
    </div>
  );
}
