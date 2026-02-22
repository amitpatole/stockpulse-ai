'use client';

import { AlertTriangle } from 'lucide-react';
import { useSSE } from '@/hooks/useSSE';

export default function ProviderStatusBadge() {
  const { fallbackActive, fallbackInfo } = useSSE();

  if (!fallbackActive || !fallbackInfo) {
    return null;
  }

  return (
    <div
      role="status"
      tabIndex={0}
      aria-label={`Data source: fallback active, using ${fallbackInfo.to_provider} (${fallbackInfo.reason})`}
      className="flex items-center gap-1.5 rounded-full bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-400 border border-amber-500/20 cursor-default focus:outline-none focus:ring-2 focus:ring-amber-500/50"
    >
      <AlertTriangle className="h-3 w-3 flex-shrink-0" aria-hidden="true" />
      <span>Fallback: {fallbackInfo.to_provider}</span>
    </div>
  );
}
