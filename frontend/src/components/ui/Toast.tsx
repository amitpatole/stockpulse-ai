```typescript
'use client';

import { useEffect, useState } from 'react';
import { CheckCircle, XCircle, AlertCircle, X } from 'lucide-react';
import { clsx } from 'clsx';

export type ToastType = 'success' | 'error' | 'info';

interface ToastProps {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
  onClose: (id: string) => void;
}

function Toast({ id, type, message, duration = 3000, onClose }: ToastProps) {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => onClose(id), duration);
      return () => clearTimeout(timer);
    }
  }, [id, duration, onClose]);

  const icons = {
    success: <CheckCircle className="h-5 w-5 text-emerald-400" aria-hidden="true" />,
    error: <XCircle className="h-5 w-5 text-red-400" aria-hidden="true" />,
    info: <AlertCircle className="h-5 w-5 text-blue-400" aria-hidden="true" />,
  };

  const bgColors = {
    success: 'bg-emerald-500/10 border-emerald-500/30',
    error: 'bg-red-500/10 border-red-500/30',
    info: 'bg-blue-500/10 border-blue-500/30',
  };

  const textColors = {
    success: 'text-emerald-300',
    error: 'text-red-300',
    info: 'text-blue-300',
  };

  const typeLabel = {
    success: 'Success',
    error: 'Error',
    info: 'Information',
  };

  return (
    <div
      className={clsx(
        'flex items-center gap-3 rounded-lg border px-4 py-3 animate-in fade-in slide-in-from-top-2 duration-300',
        bgColors[type]
      )}
      role="alert"
      aria-live="polite"
      aria-atomic="true"
    >
      {icons[type]}
      <p className={clsx('text-sm font-medium flex-1', textColors[type])}>{message}</p>
      <button
        onClick={() => onClose(id)}
        aria-label={`Close ${typeLabel[type].toLowerCase()} notification`}
        className="ml-auto text-slate-400 hover:text-slate-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-0 focus-visible:ring-blue-500"
      >
        <X className="h-4 w-4" aria-hidden="true" />
      </button>
    </div>
  );
}

interface ToastContainerProps {
  toasts: Array<{ id: string; type: ToastType; message: string }>;
  onRemove: (id: string) => void;
}

export function ToastContainer({ toasts, onRemove }: ToastContainerProps) {
  return (
    <div
      className="pointer-events-none fixed right-4 top-20 z-50 flex flex-col gap-2 max-w-sm"
      role="region"
      aria-label="Notifications"
      aria-live="polite"
      aria-atomic="false"
    >
      {toasts.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <Toast id={toast.id} type={toast.type} message={toast.message} onClose={onRemove} />
        </div>
      ))}
    </div>
  );
}

export function useToast() {
  const [toasts, setToasts] = useState<Array<{ id: string; type: ToastType; message: string }>>([]);

  const addToast = (message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts((prev) => [...prev, { id, type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const success = (message: string) => addToast(message, 'success');
  const error = (message: string) => addToast(message, 'error');
  const info = (message: string) => addToast(message, 'info');

  return { toasts, addToast, removeToast, success, error, info };
}
```