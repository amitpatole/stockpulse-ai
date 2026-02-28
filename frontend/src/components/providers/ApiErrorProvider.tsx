```tsx
'use client';

import { useEffect, useState, useCallback } from 'react';
import { setGlobalErrorReporter } from '@/lib/api';
import { ApiError } from '@/lib/types';
import Toast from '@/components/ui/Toast';

export default function ApiErrorProvider({ children }: { children: React.ReactNode }) {
  const [toast, setToast] = useState<{ message: string; variant: 'error' | 'info' } | null>(null);

  const handleError = useCallback((err: ApiError) => {
    const variant = err.status === 0 ? 'info' : 'error';
    setToast({ message: err.message, variant });
  }, []);

  const dismiss = useCallback(() => setToast(null), []);

  useEffect(() => {
    setGlobalErrorReporter(handleError);
    return () => setGlobalErrorReporter(null);
  }, [handleError]);

  return (
    <>
      {children}
      {toast && (
        <Toast message={toast.message} variant={toast.variant} onDismiss={dismiss} />
      )}
    </>
  );
}
```