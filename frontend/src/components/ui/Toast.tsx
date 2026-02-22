'use client';

import { useEffect } from 'react';
import { X } from 'lucide-react';
import { clsx } from 'clsx';

interface ToastProps {
  message: string;
  variant: 'error' | 'info';
  onDismiss: () => void;
}

export default function Toast({ message, variant, onDismiss }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 5000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div
      role="alert"
      aria-live="assertive"
      className={clsx(
        'fixed bottom-4 right-4 z-50 flex max-w-sm items-start gap-3 rounded-lg border px-4 py-3 shadow-lg',
        variant === 'error'
          ? 'border-red-800/50 bg-red-950/90 text-red-300'
          : 'border-slate-700 bg-slate-800 text-slate-300'
      )}
    >
      <p className="flex-1 text-sm">{message}</p>
      <button
        onClick={onDismiss}
        aria-label="Dismiss notification"
        className="shrink-0 text-current opacity-60 transition-opacity hover:opacity-100"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  );
}
